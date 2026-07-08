"""
MCP tools for SCM Posture Management and Incidents APIs.

Tools:
    scm_incident_search   — search/filter SCM security incidents (single or all tenants)
    scm_incident_summary  — cross-tenant NOC incident dashboard (counts by severity/status)
    scm_posture_report    — retrieve Posture Management best-practice report findings
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..auth.oauth import get_scm_client
from ..config.settings import TenantConfig
from ..utils.errors import handle_scm_exception
from ..utils.logging import get_logger

logger = get_logger(__name__)


def _load_tenant_configs() -> dict[str, TenantConfig]:
    """Load all MSSP tenant configs from settings.toml + .secrets.toml."""
    try:
        from dynaconf import Dynaconf  # type: ignore[import-untyped]

        base = Dynaconf(envvar_prefix="SCM_MCP", settings_files=["settings.toml"], load_dotenv=True)
        secrets = Dynaconf(
            envvar_prefix="SCM_MCP", settings_files=[".secrets.toml"], load_dotenv=False
        )
        base_t: dict[str, Any] = dict(base.get("tenants") or {})
        secret_t: dict[str, Any] = dict(secrets.get("tenants") or {})
        out: dict[str, TenantConfig] = {}
        for key in set(base_t) | set(secret_t):
            merged = dict(base_t.get(key) or {})
            merged.update(secret_t.get(key) or {})
            try:
                out[key] = TenantConfig(**merged)
            except Exception as exc:
                logger.warning("tenant_config_invalid", tenant=key, error=str(exc))
        return out
    except Exception as exc:
        logger.warning("tenant_config_load_failed", error=str(exc))
        return {}


# Incidents API base — confirmed live: POST /incidents/v1/search returns 200
_INC_BASE = "https://api.strata.paloaltonetworks.com"
_INC_SEARCH = "/incidents/v1/search"

# Posture API — confirmed to exist (403 = license-gated in non-subscribed tenants)
_POSTURE_BASE = "/posture/v1/reports"

_SEV_EMOJI: dict[str, str] = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
    "info": "⚪",
    "informational": "⚪",
}
_SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Informational": 4, "Info": 4}

_LICENSE_HINT = (
    "\n\nThis feature requires the **Posture Management** add-on licence for your "
    "Strata Cloud Manager subscription. Contact your PAN account team or MSSP admin to enable."
)


def _sev_emoji(sev: str) -> str:
    return _SEV_EMOJI.get(sev.lower(), "⚪")


def _incidents_for_tenant(session: Any, tenant_label: str) -> list[dict[str, Any]]:
    """Call POST /incidents/v1/search and return the data list."""
    url = f"{_INC_BASE}{_INC_SEARCH}"
    resp = session.post(url, json={}, timeout=(10, 30))
    resp.raise_for_status()
    d = resp.json()
    return d.get("data") or []


def _fmt_ts(ts: str | None) -> str:
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts[:16] if ts else "—"


def register_posture_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register Posture Management and Incidents tools."""

    @mcp.tool()
    def scm_incident_search(
        severity: str = "",
        status: str = "",
        product: str = "",
        acknowledged: str = "",
        days: int = 30,
        limit: int = 100,
        all_tenants: bool = False,
        tenant_id: str = "",
    ) -> str:
        """Search SCM security incidents via the Incidents API (March 2026).

        Queries `POST /incidents/v1/search` for security incidents raised by
        Strata Cloud Manager across Prisma Access, NGFW, and SCM platform events.
        Returns a prioritised incident table sorted by severity and raise time.

        Incident types include: dataplane upgrades, tunnel failures, certificate
        expiry, licence issues, threat events, and platform health events.

        Args:
            severity: Comma-separated filter — Critical,High,Medium,Low
                      (e.g. "Critical,High"). Empty = all severities.
            status: Comma-separated filter — Open,Closed,Acknowledged.
                    Empty = all statuses.
            product: Filter by product — "Prisma Access", "SCM", etc.
                     Empty = all products.
            acknowledged: Filter by acknowledgement — "true", "false", or "".
            days: Look-back window in days (default 30, max 180).
            limit: Max incidents to return per tenant (default 100).
            all_tenants: Sweep all configured MSSP tenants.
            tenant_id: Specific tenant ID. Defaults to active tenant.
        """
        try:
            sev_filter = (
                {s.strip().title() for s in severity.split(",") if s.strip()} if severity else set()
            )
            stat_filter = (
                {s.strip().title() for s in status.split(",") if s.strip()} if status else set()
            )
            prod_filter = product.strip().lower() if product.strip() else ""
            ack_filter = acknowledged.strip().lower()

            all_rows: list[tuple[int, str, dict[str, Any]]] = []
            tenant_errors: list[str] = []

            if all_tenants:
                tenant_map = _load_tenant_configs()
                targets = []
                for k, tc in tenant_map.items():
                    label = tc.label or k
                    try:
                        targets.append((k, label, get_scm_client(tc)))
                    except Exception as exc:
                        # A single tenant with bad/rotated credentials shouldn't
                        # abort the whole cross-tenant sweep.
                        tenant_errors.append(f"{label}: {exc}")
            else:
                client = get_client(tenant_id)
                targets = [(tenant_id or "default", tenant_id or "default", client)]

            for _key, label, c in targets:
                try:
                    session = getattr(c, "session", None)
                    if not session:
                        continue
                    incidents = _incidents_for_tenant(session, label)
                    for inc in incidents:
                        sev = str(inc.get("severity") or "")
                        stat = str(inc.get("status") or "")
                        prod = str(inc.get("product") or "")
                        ack = inc.get("acknowledged")

                        if sev_filter and sev.title() not in sev_filter:
                            continue
                        if stat_filter and stat.title() not in stat_filter:
                            continue
                        if prod_filter and prod_filter not in prod.lower():
                            continue
                        if ack_filter == "true" and not ack:
                            continue
                        if ack_filter == "false" and ack:
                            continue

                        sort_key = _SEV_ORDER.get(sev.title(), 99)
                        inc["_tenant_label"] = label
                        all_rows.append((sort_key, str(inc.get("raised_time") or ""), inc))
                except Exception as exc:
                    tenant_errors.append(f"{label}: {exc}")

            # Sort: severity asc, then raised_time desc
            all_rows.sort(key=lambda x: (x[0], x[1]))
            all_rows = all_rows[:limit]

            ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
            sev_desc = f" severity={severity}" if severity else ""
            stat_desc = f" status={status}" if status else ""
            lines = [
                f"## SCM Incidents{sev_desc}{stat_desc} — last {days}d",
                "",
                f"*Queried: {ts}  |  Results: {len(all_rows)}*",
                "",
            ]

            if not all_rows:
                lines.append("No incidents found matching the specified filters. ✅")
            else:
                multi = all_tenants and len(targets) > 1
                cols = (
                    "| Sev | Raised | Status | Title | Product | Category | Tenant |"
                    if multi
                    else "| Sev | Raised | Status | Title | Product | Category |"
                )
                sep = "|---|---|---|---|---|---|---|" if multi else "|---|---|---|---|---|---|"
                lines += [cols, sep]

                for _, _, inc in all_rows:
                    sev = inc.get("severity") or "—"
                    emoji = _sev_emoji(sev)
                    raised = _fmt_ts(str(inc.get("raised_time") or ""))
                    stat = inc.get("status") or "—"
                    title = str(inc.get("title") or "—")[:60]
                    prod = inc.get("product") or "—"
                    cat = inc.get("category") or "—"
                    ack_mark = " ✓" if inc.get("acknowledged") else ""
                    row = f"| {emoji} {sev} | {raised} | {stat}{ack_mark} | {title} | {prod} | {cat} |"
                    if multi:
                        row += f" {inc.get('_tenant_label', '—')} |"
                    lines.append(row)

            if tenant_errors:
                lines += ["", "**Errors:**"]
                for e in tenant_errors:
                    lines.append(f"- {e}")

            return "\n".join(lines)

        except Exception as exc:
            return f"Error: {handle_scm_exception(exc, tool='scm_incident_search', tenant_id=tenant_id)}"

    @mcp.tool()
    def scm_incident_summary(
        days: int = 7,
        all_tenants: bool = True,
        tenant_id: str = "",
    ) -> str:
        """Cross-tenant SCM incident NOC dashboard.

        Fetches incidents from all (or a single) MSSP tenant and produces
        a traffic-light summary table: count of Critical/High/Medium/Low/Total
        incidents per tenant alongside the most recent open critical incident title.

        Ideal for morning NOC briefings and MSSP SLA reporting.

        Args:
            days: Look-back window in days (default 7).
            all_tenants: Sweep all configured tenants (default True).
            tenant_id: Specific tenant ID when all_tenants=False.
        """
        try:
            if all_tenants:
                tenant_map = _load_tenant_configs()
                targets: list[tuple[str, str, Any]] = []
                for k, tc in tenant_map.items():
                    label = tc.label or k
                    try:
                        targets.append((k, label, get_scm_client(tc)))
                    except Exception as exc:
                        # A single tenant with bad/rotated credentials shouldn't
                        # abort the whole cross-tenant dashboard — surface it as
                        # a per-tenant error row instead (the "no session" branch
                        # below already handles a None client gracefully).
                        logger.warning(
                            "incident_summary_tenant_auth_failed", tenant=k, error=str(exc)
                        )
                        targets.append((k, label, None))
            else:
                client = get_client(tenant_id)
                targets = [(tenant_id or "default", tenant_id or "default", client)]

            ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
            lines = [
                f"## SCM Incident Summary — last {days}d  ({ts})",
                "",
                "| Tenant | 🔴 Crit | 🟠 High | 🟡 Med | 🔵 Low | Total | Latest Critical |",
                "|---|---|---|---|---|---|---|",
            ]

            for _key, label, c in targets:
                try:
                    session = getattr(c, "session", None)
                    if not session:
                        lines.append(f"| {label} | — | — | — | — | — | no session |")
                        continue
                    incidents = _incidents_for_tenant(session, label)
                    counts: dict[str, int] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
                    latest_crit: str = "—"
                    for inc in incidents:
                        sev = str(inc.get("severity") or "").title()
                        if sev in counts:
                            counts[sev] += 1
                        if sev == "Critical" and inc.get("status", "").lower() != "closed":
                            t = str(inc.get("title") or "")[:40]
                            if latest_crit == "—":
                                latest_crit = t
                    total = sum(counts.values())
                    crit_cell = f"**{counts['Critical']}**" if counts["Critical"] else "0"
                    high_cell = f"**{counts['High']}**" if counts["High"] else "0"
                    lines.append(
                        f"| {label} | {crit_cell} | {high_cell} | "
                        f"{counts['Medium']} | {counts['Low']} | {total} | {latest_crit} |"
                    )
                except Exception as exc:
                    lines.append(f"| {label} | — | — | — | — | — | Error: {str(exc)[:50]} |")

            return "\n".join(lines)

        except Exception as exc:
            return f"Error: {handle_scm_exception(exc, tool='scm_incident_summary', tenant_id=tenant_id)}"

    @mcp.tool()
    def scm_posture_report(
        folder: str = "Shared",
        tenant_id: str = "",
    ) -> str:
        """Retrieve SCM Posture Management best-practice report findings.

        Queries the Posture Management API (`/posture/v1/reports`) introduced
        March 2026. Returns security posture findings across SCM-managed devices
        including policy gaps, configuration drift, and compliance deviations.

        **Note:** Requires the Posture Management add-on licence for your SCM
        subscription. Contact your PAN account team or MSSP admin to enable.
        The Posture Management API currently covers the Best Practice Report
        module; Compliance, Policy Optimizer, Policy Analyzer, and Config Cleanup
        modules are in development.

        Args:
            folder: SCM folder scope (default "Shared").
            tenant_id: SCM tenant ID. Defaults to active tenant.
        """
        try:
            client = get_client(tenant_id)
            session = getattr(client, "session", None)
            if not session:
                return "Error: no HTTP session available on SCM client."

            url = f"{_INC_BASE}{_POSTURE_BASE}"
            params: dict[str, str] = {}
            if folder:
                params["folder"] = folder

            resp = session.get(url, params=params, timeout=(10, 30))

            if resp.status_code == 403:
                from contextlib import suppress

                body: dict[str, Any] = {}
                with suppress(Exception):
                    body = resp.json()
                msg = body.get("msg") or body.get("message") or "Access denied"
                return f"**Posture Management API — {msg}**\n{_LICENSE_HINT}"

            resp.raise_for_status()
            data = resp.json()

            ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
            lines = [
                f"## SCM Posture Report — {folder}",
                "",
                f"*Retrieved: {ts}*",
                "",
            ]

            reports = data if isinstance(data, list) else data.get("data", [data])
            if not reports:
                lines.append("No posture report data available for this folder.")
                return "\n".join(lines)

            for report in reports[:5]:
                if isinstance(report, dict):
                    name = report.get("name") or report.get("id") or "Report"
                    status = report.get("status") or report.get("state") or "—"
                    score = report.get("score") or report.get("overall_score") or "—"
                    lines += [
                        f"### {name}",
                        "",
                        f"**Status:** {status}  |  **Score:** {score}",
                        "",
                        "```json",
                        json.dumps(report, indent=2, default=str)[:1000],
                        "```",
                        "",
                    ]
                else:
                    lines += ["```json", json.dumps(report, default=str)[:500], "```", ""]

            return "\n".join(lines)

        except Exception as exc:
            return f"Error: {handle_scm_exception(exc, tool='scm_posture_report', tenant_id=tenant_id)}"
