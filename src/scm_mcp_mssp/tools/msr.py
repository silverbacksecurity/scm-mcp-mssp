"""MCP tool for the MSR — Monthly Service Review pack (``scm_msr_report``).

Assembles the per-tenant monthly customer deliverable from sources the
server already produces: period-bounded incidents and config jobs, the
SSR provenance ledger, compliance posture (tier-gated depth), licence
expiry, and the Insights bandwidth snapshot. Every source degrades
gracefully — a licence-API outage costs one section, not the pack.

Pure period/SLA/rendering logic lives in ``audit/msr_report.py``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..audit.insights_extractor import extract_insights
from ..audit.msr_report import MsrData, in_period, month_bounds, parse_ssr_notes, render_msr_report
from ..auth.oauth import fetch_licenses
from ..config.settings import load_all_tenant_configs
from ..utils.errors import handle_scm_exception
from ..utils.logging import get_logger
from .compliance import _compliance_get
from .ops import _licence_rows
from .posture import _incidents_for_tenant
from .ssr import _get_ssr_config, _resolve_default_folder

logger = get_logger(__name__)

# ssr_objects key → (SCM SDK resource attribute, fetch kwarg style)
_SSR_OBJECT_RESOURCES = {
    "url_allow_list": "url_category",
    "url_block_list": "url_category",
    "anti_spyware_profile": "anti_spyware_profile",
    "vulnerability_protection_profile": "vulnerability_protection_profile",
    "ssl_decrypt_exclude_rule": "decryption_rule",
}


def _resolve_tenant_meta(tenant_id: str) -> tuple[str, str, str, str]:
    """Return (label, tsg_id, tier, insights_region) for *tenant_id*.

    Same single-tenant fallback rule as the SSR tool: empty tenant_id maps
    to the first configured tenant; an explicit non-matching tenant_id
    returns empty metadata rather than another tenant's.
    """
    tenants = load_all_tenant_configs()
    tc = None
    if tenant_id:
        tc = next((t for t in tenants.values() if t.tenant_id == tenant_id), None)
    elif tenants:
        tc = next(iter(tenants.values()))
    if tc is None:
        return "", tenant_id, "bronze", "eu"
    tier = getattr(tc.tier, "value", None) or str(tc.tier)
    return tc.label or tc.tenant_id, tc.tenant_id, tier.lower(), tc.insights_region


def _gather_ssr_ledger(client: Any, tenant_id: str) -> list[dict[str, str]]:
    """Parse SSR provenance notes off every configured SSR-managed object."""
    ssr_config = _get_ssr_config(tenant_id)
    if not ssr_config:
        return []
    folder = _resolve_default_folder(tenant_id)
    ledger: list[dict[str, str]] = []
    for key, obj_name in ssr_config.items():
        resource_attr = _SSR_OBJECT_RESOURCES.get(key)
        if not resource_attr or not obj_name:
            continue
        try:
            obj = getattr(client, resource_attr).fetch(name=obj_name, folder=folder)
            desc = (obj.model_dump() or {}).get("description") or ""
            ledger.extend(parse_ssr_notes(desc, obj_name))
        except Exception as exc:
            logger.warning("msr_ssr_object_failed", object=obj_name, error=str(exc))
    return ledger


def gather_msr_data(
    client: Any,
    tenant_id: str = "",
    month: str = "",
    mssp_name: str = "MSSP",
    include_insights: bool = True,
) -> MsrData:
    """Gather every MSR source for the period, degrading per-source."""
    start, end, label = month_bounds(month)
    tenant_label, tsg_id, tier, region = _resolve_tenant_meta(tenant_id)
    data = MsrData(
        tenant_label=tenant_label,
        tenant_id=tsg_id,
        tier=tier,
        mssp_name=mssp_name,
        period_start=start,
        period_end=end,
        period_label=label,
    )

    # ── Incidents (period-bounded) ──────────────────────────────────────
    try:
        session = getattr(client, "session", None)
        if session is None:
            raise RuntimeError("client has no HTTP session")
        raw = _incidents_for_tenant(session, tenant_label)
        data.incidents = [i for i in raw if in_period(i.get("raised_time"), start, end)]
        data.gathered.append(f"incidents — {len(data.incidents)} in period (Incidents API)")
    except Exception as exc:
        data.errors["incidents"] = str(exc)

    # ── Config jobs (period-bounded) ────────────────────────────────────
    try:
        response = client.list_jobs(limit=200)
        jobs = response.data if hasattr(response, "data") else []
        rows = [
            {
                "job_id": getattr(j, "id", ""),
                "type": getattr(j, "type_str", getattr(j, "job_type", "")),
                "result": getattr(j, "result_str", ""),
                "user": getattr(j, "uname", ""),
                "description": getattr(j, "description", ""),
                "start_ts": str(getattr(j, "start_ts", "")),
                "end_ts": str(getattr(j, "end_ts", "")),
            }
            for j in jobs
        ]
        data.jobs = [r for r in rows if in_period(r["start_ts"], start, end)]
        data.gathered.append(f"config jobs — {len(data.jobs)} in period (Jobs API)")
    except Exception as exc:
        data.errors["jobs"] = str(exc)

    # ── SSR ledger (cumulative provenance) ──────────────────────────────
    try:
        data.ssr_ledger = _gather_ssr_ledger(client, tenant_id)
        if data.ssr_ledger:
            data.gathered.append(f"SSR ledger — {len(data.ssr_ledger)} provenance notes")
    except Exception as exc:
        data.errors["ssr_ledger"] = str(exc)

    # ── Licences ────────────────────────────────────────────────────────
    try:
        data.licence_rows = _licence_rows(fetch_licenses(client))
        data.gathered.append(f"licences — {len(data.licence_rows)} SKU groups (Subscription API)")
    except Exception as exc:
        data.errors["licences"] = str(exc)

    # ── Bandwidth + connected MU (Insights snapshot) ────────────────────
    if include_insights:
        try:
            ins = extract_insights(client, tenant_id=tsg_id, region=region)
            data.bandwidth_rows = list(ins.location_rn_bandwidth) + list(ins.location_sc_bandwidth)
            data.connected_mu = ins.connected_mu_count if ins.connected_mu_count >= 0 else None
            # Only bandwidth-endpoint failures belong in this section's error —
            # extract_insights also probes MU/tunnel/alert endpoints whose
            # errors (RBAC 403s etc.) must not mask a legitimate 0-row result.
            bw_errors = [e for e in ins.errors if "_bw" in e or "bandwidth" in e]
            if bw_errors and not data.bandwidth_rows:
                data.errors["bandwidth"] = "; ".join(bw_errors[:3])
            else:
                data.gathered.append(
                    f"bandwidth — {len(data.bandwidth_rows)} location rows (Insights v3, 24h window)"
                )
        except Exception as exc:
            data.errors["bandwidth"] = str(exc)
    else:
        data.errors["bandwidth"] = "skipped (include_insights=False)"

    # ── Compliance (Silver+; Gold gets the trend annex) ────────────────
    if tier != "bronze":
        try:
            raw = _compliance_get(client, "/summaries", {"product": "all"})
            items = raw if isinstance(raw, list) else (raw or {}).get("data") or []
            data.compliance_summaries = items
            data.gathered.append(f"compliance — {len(items)} frameworks (Compliance Center API)")
            if tier == "gold":
                bench = next((i for i in items if i.get("benchmark")), None)
                if bench:
                    revisions = bench.get("revision_summary") or []
                    data.compliance_framework_name = str(
                        (revisions[0] if revisions else {}).get("name") or bench.get("id") or ""
                    )
                    tl = _compliance_get(
                        client,
                        f"/overall-compliance-timeline/{bench.get('id')}",
                        {"product": "all"},
                    )
                    data.compliance_timeline = (tl or {}).get("timeline_30_days") or []
        except Exception as exc:
            data.errors["compliance"] = str(exc)

    return data


def register_msr_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register the MSR tool — ``scm_msr_report``."""

    @mcp.tool()
    def scm_msr_report(
        tenant_id: str = "",
        month: str = "",
        mssp_name: str = "MSSP",
        output_format: str = "markdown",
        save_to: str = "",
        include_insights: bool = True,
    ) -> str:
        """Generate the Monthly Service Review pack for a customer tenant.

        Assembles the monthly customer deliverable from live tenant data:

          1. Executive summary — ranked headline bullets (worst first)
          2. Service statistics — incidents, MTTR, ack rate, change failure rate
          3. Incidents raised in the period (severity-ranked)
          4. Change record — config jobs in period + cumulative SSR ledger
          5. Compliance posture — Silver+ (Gold adds the 30-day score trend)
          6. Licence & renewal posture — expiries within 180 days, flagged
          7. Bandwidth consumption — per-location Insights snapshot (24h)
          8. Data-source coverage — what was gathered vs unavailable

        Every source degrades gracefully: an unavailable API costs one
        section (disclosed in §8), never the whole pack.

        Args:
            tenant_id: SCM tenant ID. Defaults to the first configured tenant.
            month: Review period as ``YYYY-MM`` (e.g. "2026-06"). Defaults to
                   the previous full calendar month.
            mssp_name: Service-provider name for the header.
            output_format: 'markdown' (default) or 'docx' (pandoc via the
                           bundled pypandoc-binary).
            save_to: Optional output path. Defaults for docx to
                     'reports/<tenant>-msr-<period>.docx'; markdown returns
                     inline unless a path is given.
            include_insights: Set False to skip the Insights bandwidth/MU
                              calls (faster; §7 is marked skipped).
        """
        try:
            start_end_label = month_bounds(month)
        except ValueError as exc:
            return f"Error: {exc}"
        period_label = start_end_label[2]

        try:
            client = get_client(tenant_id)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc, tool='scm_msr_report', tenant_id=tenant_id)}"

        data = gather_msr_data(
            client,
            tenant_id=tenant_id,
            month=month,
            mssp_name=mssp_name,
            include_insights=include_insights,
        )
        report_md = render_msr_report(data)

        if output_format.lower() == "docx":
            from .audit import _md_to_docx

            slug = re.sub(r"[^a-zA-Z0-9-]+", "-", data.tenant_label or "tenant").strip("-").lower()
            out_path = (
                Path(save_to) if save_to else Path("reports") / f"{slug}-msr-{period_label}.docx"
            )
            try:
                result = _md_to_docx(report_md, out_path)
            except Exception as exc:
                return f"Error converting to DOCX: {exc}\n\n{report_md}"
            return f"MSR pack for {data.tenant_label} ({period_label}) saved to `{result}`."

        if save_to:
            Path(save_to).parent.mkdir(parents=True, exist_ok=True)
            Path(save_to).write_text(report_md)
            return f"MSR pack for {data.tenant_label} ({period_label}) saved to `{save_to}`."
        return report_md
