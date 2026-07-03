"""
MCP tools for SCM Objects resources.

Covers: addresses, address groups, services, service groups, tags,
        applications, application groups, application filters,
        external dynamic lists (EDLs), HIP objects, HIP profiles.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..utils.errors import handle_scm_exception
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_object_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register all SCM Objects tools onto the MCP server."""

    # ── Addresses ──────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_address_list(
        folder: str,
        tenant_id: str = "",
        limit: int = 200,
        name_filter: str = "",
    ) -> str:
        """List address objects in a SCM folder.

        Args:
            folder: SCM folder (customer context for MSSP).
            tenant_id: SCM tenant ID; uses default tenant when omitted.
            limit: Maximum number of results.
            name_filter: Substring filter on address name.
        """
        try:
            client = get_client(tenant_id)
            results = client.address.list(folder=folder, limit=limit)
            if name_filter:
                results = [r for r in results if name_filter.lower() in r.name.lower()]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_address_get(name: str, folder: str, tenant_id: str = "") -> str:
        """Fetch a single address object by name.

        Args:
            name: Address object name.
            folder: SCM folder.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            obj = client.address.fetch(name=name, folder=folder)
            return _fmt(obj)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_address_create(
        name: str,
        folder: str,
        ip_netmask: str = "",
        fqdn: str = "",
        ip_range: str = "",
        description: str = "",
        tenant_id: str = "",
    ) -> str:
        """Create an address object in SCM.

        Provide exactly one of ip_netmask, fqdn, or ip_range.

        Args:
            name: Object name.
            folder: SCM folder.
            ip_netmask: CIDR notation (e.g. 10.0.0.0/8).
            fqdn: Fully qualified domain name.
            ip_range: IP range (e.g. 10.0.0.1-10.0.0.100).
            description: Optional description.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            payload: dict[str, Any] = {"name": name, "folder": folder}
            if ip_netmask:
                payload["ip_netmask"] = ip_netmask
            elif fqdn:
                payload["fqdn"] = fqdn
            elif ip_range:
                payload["ip_range"] = ip_range
            else:
                return "Error: supply one of ip_netmask, fqdn, or ip_range"
            if description:
                payload["description"] = description
            obj = client.address.create(payload)
            logger.info("address_created", name=name, folder=folder)
            return _fmt(obj)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_address_delete(name: str, folder: str, tenant_id: str = "") -> str:
        """Delete an address object by name.

        Args:
            name: Address object name.
            folder: SCM folder.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            obj = client.address.fetch(name=name, folder=folder)
            client.address.delete(obj.id)
            logger.info("address_deleted", name=name, folder=folder)
            return f"Deleted address '{name}' from folder '{folder}'"
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── Address Groups ──────────────────────────────────────────────────────

    @mcp.tool()
    def scm_address_group_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List address groups in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum number of results.
        """
        try:
            client = get_client(tenant_id)
            results = client.address_group.list(folder=folder, limit=limit)
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── Services ────────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_service_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List service objects in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum number of results.
        """
        try:
            client = get_client(tenant_id)
            results = client.service.list(folder=folder, limit=limit)
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── Tags ────────────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_tag_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List tags in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum number of results.
        """
        try:
            client = get_client(tenant_id)
            results = client.tag.list(folder=folder, limit=limit)
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── External Dynamic Lists ──────────────────────────────────────────────

    @mcp.tool()
    def scm_edl_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List external dynamic lists (EDLs) in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum number of results.
        """
        try:
            client = get_client(tenant_id)
            # SDK accessor is singular `external_dynamic_list`; list() has no limit kwarg.
            results = client.external_dynamic_list.list(folder=folder)[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"


def _fmt(data: Any) -> str:
    """Serialise a Pydantic model, list of models, or plain dict to a string."""
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
