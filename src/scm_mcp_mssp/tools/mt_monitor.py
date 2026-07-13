"""
Cross-tenant aggregate monitoring — the `sase/mt-monitor` family.

MSP-level analytics aggregated across a parent tenant and its children
(`agg_by=tenant`): application usage/risk, threats, GlobalProtect users by
location, SD-WAN/Prisma Access service connectivity, and incident counts.
Only the alerts sub-resource was previously wired (compliance snapshots);
this module surfaces the analytics surface as a tool.

Quirks learned live:
- Data lives in a CDL region selected by the `X-PANW-Region` header
  (de/americas/europe/uk/sg/ca/jp/au/in, default americas). A tenant whose
  `insights_region` says `eu` may still store data in `uk` (true for the
  BT labs), so when no region is given we try the mapped region and its
  eu/uk sibling and keep the first non-empty answer.
- Requests use the aggregation query language from the spec examples:
  `{"filter": {"rules": [...]}, "properties": [...]}`; wrong/missing
  properties → HTTP 400.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..audit.extractor import _bearer_session_for
from ..utils.formatting import format_result as _fmt
from ..utils.logging import get_logger

logger = get_logger(__name__)

_BASE = "https://api.sase.paloaltonetworks.com/mt/monitor/v1/agg"
_REGION_MAP = {"eu": "europe", "uk": "uk", "us": "americas", "sg": "sg", "au": "au"}
_CDL_REGIONS = ("de", "americas", "europe", "uk", "sg", "ca", "jp", "au", "in")


def _days_filter(days: int, prop: str = "event_time") -> dict[str, Any]:
    return {"operator": "last_n_days", "property": prop, "values": [days]}


def _view_queries(view: str, days: int) -> list[tuple[str, str, dict[str, Any]]]:
    """(result_key, path, body) triples per view — bodies follow the spec examples."""
    if view == "apps":
        return [
            (
                "summary",
                "applications/summary",
                {
                    "filter": {"operator": "AND", "rules": [_days_filter(days)]},
                    "properties": [
                        {"property": "total_app_count"},
                        {"property": "risk_of_app_count"},
                        {"property": "blocked_app_count"},
                    ],
                },
            ),
        ]
    if view == "threats":
        return [
            (
                "summary",
                "threats/summary",
                {
                    "filter": {
                        "operator": "AND",
                        "rules": [
                            {
                                "operator": "in",
                                "property": "severity",
                                "values": ["Critical", "High", "Medium"],
                            },
                            _days_filter(days),
                        ],
                    },
                    "properties": [
                        {"property": "total_threats"},
                        {"property": "blocked_count"},
                    ],
                },
            )
        ]
    if view == "connectivity":
        return [
            (
                "sites_by_state",
                "serviceConnectivity",
                {
                    "filter": {
                        "rules": [
                            {"operator": "in", "property": "node_type", "values": [51, 48]},
                            {
                                "operator": "in",
                                "property": "site_state_name",
                                "values": ["Up", "Down"],
                            },
                        ]
                    },
                    "properties": [
                        {"property": "node_type"},
                        {"property": "sub_tenant_id"},
                        {"alias": "count", "function": "distinct_count", "property": "site_name"},
                    ],
                },
            )
        ]
    if view == "incidents":
        return [
            (
                "counts",
                "incidents/count",
                {
                    "filter": {
                        "rules": [
                            _days_filter(days, prop="raised_time"),
                            {"operator": "equals", "property": "status", "values": ["Raised"]},
                            {
                                "operator": "in",
                                "property": "severity",
                                "values": ["Critical", "Warning"],
                            },
                            {
                                "operator": "in",
                                "property": "domain",
                                "values": ["External", "external"],
                            },
                        ]
                    },
                    "properties": [
                        {"property": "total_count"},
                        {"property": "critical_count"},
                        {"property": "warning_count"},
                    ],
                },
            )
        ]
    return []


def register_mt_monitor_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register cross-tenant MT Monitor analytics tools."""

    @mcp.tool()
    def scm_mt_analytics(
        tenant_id: str = "",
        view: str = "apps",
        days: int = 7,
        region: str = "",
    ) -> str:
        """Cross-tenant analytics aggregated over the MSP tenant hierarchy.

        Queries the MT Monitor aggregation API with `agg_by=tenant`, so a
        parent (MSSP) tenant answers for itself and all child tenants.

        Views:
        - apps: total / risky / blocked application counts.
        - threats: total and blocked threat counts (Critical/High/Medium).
        - connectivity: site counts by node type and up/down state per
          child tenant.
        - incidents: raised incident counts by severity.

        (applications/list and locationsUsers are omitted: both reject or
        500 on the spec's own example payloads — revisit on a spec update.)

        Data resides in a CDL region (X-PANW-Region). If `region` is not
        given, the tenant's insights_region is mapped (eu→europe etc.) and
        its eu/uk sibling is also tried, keeping the first non-empty
        answer — e.g. BT lab tenants say `eu` but hold data in `uk`.

        Args:
            tenant_id: SCM tenant ID (MSSP parent).
            view: apps | threats | connectivity | incidents.
            days: Look-back window in days (default 7).
            region: CDL region override (de, americas, europe, uk, sg,
                ca, jp, au, in).

        Returns:
            JSON with the view's result sets and the region that answered.
        """
        try:
            queries = _view_queries(view, days)
            if not queries:
                return "Error: view must be one of apps, threats, connectivity, incidents"
            if region and region not in _CDL_REGIONS:
                return f"Error: region must be one of {', '.join(_CDL_REGIONS)}"

            client = get_client(tenant_id)
            session = _bearer_session_for(client)

            if region:
                candidates = [region]
            else:
                mapped = "europe"
                try:
                    from ..config.settings import load_all_tenant_configs

                    cfgs = load_all_tenant_configs()
                    tc = cfgs.get(tenant_id) or next(
                        (c for c in cfgs.values() if c.tenant_id == tenant_id), None
                    )
                    if tc is not None:
                        mapped = _REGION_MAP.get(tc.insights_region, "europe")
                except Exception:
                    pass
                sibling = {"europe": ["uk"], "uk": ["europe"]}.get(mapped, [])
                candidates = [mapped, *sibling]

            result: dict[str, Any] = {"view": view, "window_days": days}
            warnings: list[str] = []
            for cand in candidates:
                data: dict[str, Any] = {}
                hits = 0
                for key, path, body in queries:
                    resp = session.post(
                        f"{_BASE}/{path}",
                        params={"agg_by": "tenant"},
                        headers={"X-PANW-Region": cand},
                        json=body,
                        timeout=(5, 30),
                    )
                    if resp.status_code != 200:
                        warnings.append(f"{path} [{cand}]: HTTP {resp.status_code}")
                        data[key] = []
                        continue
                    rows = (resp.json() or {}).get("data") or []
                    data[key] = rows
                    hits += len(rows)
                if hits or cand == candidates[-1]:
                    result["region"] = cand
                    result.update(data)
                    if not hits:
                        result["note"] = (
                            f"no datapoints in regions {', '.join(candidates)} for the last "
                            f"{days} day(s) — pass region= explicitly if the tenant's CDL "
                            "region differs from its insights_region"
                        )
                    break
            if warnings:
                result["warnings"] = warnings
            return _fmt(result)
        except Exception as exc:
            return f"Error: {exc}"
