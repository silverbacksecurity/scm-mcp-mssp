"""
MCP tools for SCM Network resources.

Covers: security zones, NAT rules, static routes, BGP, interfaces,
        IKE gateways, IPSec tunnels, DNS servers.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..utils.errors import handle_scm_exception
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_network_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register all SCM Network tools onto the MCP server."""

    # ── Security Zones ──────────────────────────────────────────────────────

    @mcp.tool()
    def scm_zone_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List security zones in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            results = client.security_zone.list(folder=folder, limit=limit)
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── NAT Rules ───────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_nat_rule_list(
        folder: str,
        tenant_id: str = "",
        limit: int = 200,
        position: str = "pre",
    ) -> str:
        """List NAT rules in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
            position: Rule position — 'pre' or 'post'.
        """
        try:
            client = get_client(tenant_id)
            results = client.nat_rule.list(folder=folder, limit=limit, position=position)
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_nat_rule_get(name: str, folder: str, tenant_id: str = "") -> str:
        """Fetch a single NAT rule by name.

        Args:
            name: NAT rule name.
            folder: SCM folder.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            obj = client.nat_rule.fetch(name=name, folder=folder)
            return _fmt(obj)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── IKE / IPSec ─────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_ike_gateway_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List IKE gateways in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # IKEGateway.list() does not accept a limit kwarg — slice client-side.
            results = client.ike_gateway.list(folder=folder)[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_ipsec_tunnel_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List IPSec tunnels in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            results = client.ipsec_tunnel.list(folder=folder, limit=limit)
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── DNS Servers ─────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_dns_server_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List internal DNS servers for the tenant.

        Internal DNS servers are a deployment-global resource (not folder-scoped),
        so the ``folder`` argument is accepted for interface consistency but not
        used to filter results.

        Args:
            folder: SCM folder (unused — kept for interface consistency).
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # SDK accessor is `internal_dns_server`; its list() has no limit kwarg.
            results = client.internal_dns_server.list()[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"


def _fmt(data: Any) -> str:
    import json

    if hasattr(data, "model_dump"):
        return json.dumps(data.model_dump(), indent=2, default=str)
    if isinstance(data, list):
        return json.dumps(
            [d.model_dump() if hasattr(d, "model_dump") else d for d in data],
            indent=2,
            default=str,
        )
    return json.dumps(data, indent=2, default=str)
