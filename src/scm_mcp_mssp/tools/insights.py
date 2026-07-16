"""MCP tool for Prisma Access Insights — general-purpose query interface.

A single tool (``scm_insights_query``) that unlocks all 103 Insights query
paths (v1.0 / v2.0 / v3.0 + custom queries + exports) behind one ergonomic
interface.  Replaces the 5 hardcoded queries in ``ops.py`` with a
general-purpose dispatch.

API base: ``https://api.sase.paloaltonetworks.com/insights/v3.0/resource/query``
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..utils.errors import handle_scm_exception
from ..utils.formatting import format_result as _fmt
from ..utils.logging import get_logger

logger = get_logger(__name__)

_INSIGHTS_BASE_V3 = "https://api.sase.paloaltonetworks.com/insights/v3.0/resource"
_INSIGHTS_BASE_V2 = "https://api.sase.paloaltonetworks.com/api/sase/v2.0/resource"
_INSIGHTS_BASE_V1 = "https://api.sase.paloaltonetworks.com/api/sase/v1.0/resource"

_REGION_MAP = {"eu": "europe", "uk": "uk", "us": "americas", "sg": "sg", "au": "au"}


def _refresh_token(client: Any) -> None:
    """Refresh the OAuth token before direct-session calls.

    is_expired/token_expires_soon can miss stale tokens (see
    scm_mobile_user_stats) — always attempt an unconditional refresh so a
    long-lived server session never hits TokenExpiredError mid-request.
    """
    oauth = getattr(client, "oauth_client", None)
    if oauth is None:
        return
    try:
        oauth.refresh_token()
    except Exception:
        try:
            if oauth.is_expired or oauth.token_expires_soon:
                oauth.refresh_token()
        except Exception:  # noqa: S110 - best-effort; the request surfaces auth errors
            pass


def _insights_call(
    session: Any,
    path: str,
    tenant_id: str,
    body: dict | None = None,
    region: str = "europe",
    timeout: tuple[int, int] = (10, 30),
) -> tuple[int, Any]:
    """POST to Insights, returning (status_code, parsed_json_or_text)."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-PANW-Region": region,
    }
    if tenant_id:  # never send an empty Prisma-Tenant header
        headers["Prisma-Tenant"] = str(tenant_id)
    resp = session.post(path, json=body or {}, headers=headers, timeout=timeout)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text


def register_insights_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register the Insights general-purpose query tool."""

    @mcp.tool()
    def scm_insights_query(
        resource: str,
        tenant_id: str = "",
        body: str = "",
        api_version: str = "v3",
        region: str = "",
    ) -> str:
        """Run an arbitrary Prisma Access Insights query.

        Unlocks all 103 Insights paths (v1.0 / v2.0 / v3.0 + custom queries
        + scheduled exports) behind one general-purpose interface.

        **Common resource paths (v3.0):**
        - ``gp_mobileusers/connected_user_count`` — GP mobile user count
        - ``users/agent/connected_user_count`` — PA Agent connected users
        - ``gp_mobileusers/user_list`` — GP user list with locations
        - ``users/agent/user_list`` — PA Agent user list
        - ``pa_bandwidth_consumption`` — per-SPN bandwidth
        - ``agents/agent_versions`` — agent version distribution
        - ``tunnels/tunnel_list`` — IKE tunnel status (needs scope)

        **v2.0 / v1.0 format:**
        - ``query/{resource_name}`` — POST to named resource
        - ``custom/query/{feature}/{request}`` — custom query
        - ``download`` — export download

        **Scheduled exports (v2.0):**
        - ``export/schedule/query/{resource_name}`` — schedule an export
        - ``download/status`` — check download status

        Args:
            resource: Insights resource path (everything after /query/ or
                /resource/). E.g. ``gp_mobileusers/connected_user_count``.
            tenant_id: SCM tenant ID. Defaults to active tenant.
            body: JSON string of query filters (default ``{}``). The
                Insights API uses a simple ``{"key": "value"}`` filter
                format — see pan.dev for per-resource filter schemas.
            api_version: API version — v1 | v2 | v3 (default v3).
            region: X-PANW-Region override (europe, americas, uk, sg, au).
                Defaults to tenant's insights_region.

        Returns:
            JSON with ``resource``, ``data`` array, and ``region`` used.
        """
        import json

        try:
            # --- Resolve client ---
            client = get_client(tenant_id)
            session = getattr(client, "session", None)
            if not session:
                return "Error: no HTTP session available on SCM client."
            _refresh_token(client)

            # --- Resolve region ---
            if not region:
                region = "europe"
                try:
                    from ..config.settings import load_all_tenant_configs

                    cfgs = load_all_tenant_configs()
                    if tenant_id:
                        tc = next((c for c in cfgs.values() if c.tenant_id == tenant_id), None)
                    else:
                        tc = next(iter(cfgs.values()), None) if cfgs else None
                    if tc is not None:
                        region = _REGION_MAP.get(tc.insights_region, "europe")
                except Exception:
                    pass

            # --- Resolve base URL ---
            version = api_version.strip().lower()
            if version == "v2":
                base = _INSIGHTS_BASE_V2
            elif version == "v1":
                base = _INSIGHTS_BASE_V1
            else:
                base = _INSIGHTS_BASE_V3

            # --- Parse body ---
            body_dict: dict | None = None
            if body.strip():
                try:
                    body_dict = json.loads(body)
                except json.JSONDecodeError as exc:
                    return f"Error: invalid JSON in `body`: {exc}"

            # --- Build URL ---
            resource_clean = resource.strip().lstrip("/")
            if version in ("v1", "v2"):
                # v1/v2: /api/sase/v{X}.0/resource/{resource}
                path = f"{base}/{resource_clean}"
            else:
                # v3: /insights/v3.0/resource/query/{resource}
                path = f"{base}/query/{resource_clean}"

            # --- Call ---
            status, data = _insights_call(session, path, tenant_id, body_dict, region)

            if status != 200:
                return _fmt(
                    {
                        "resource": resource,
                        "api_version": api_version,
                        "region": region,
                        "error": f"HTTP {status}",
                        "detail": data if isinstance(data, str) else str(data)[:500],
                    }
                )

            rows = data.get("data", data) if isinstance(data, dict) else data
            return _fmt(
                {
                    "resource": resource,
                    "api_version": api_version,
                    "region": region,
                    "count": len(rows) if isinstance(rows, list) else 0,
                    "data": rows,
                }
            )

        except Exception as exc:
            return f"Error: {handle_scm_exception(exc, tool='scm_insights_query', tenant_id=tenant_id)}"
