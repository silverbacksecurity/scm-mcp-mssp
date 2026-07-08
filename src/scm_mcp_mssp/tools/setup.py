"""
MCP tools for SCM Setup resources and MSSP tenant management.

Covers: folders (tenant hierarchy), snippets, devices, variables,
        and MSSP-specific tenant lifecycle helpers.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..auth.oauth import evict_tenant, list_loaded_tenants
from ..utils.errors import handle_scm_exception
from ..utils.formatting import format_result as _fmt
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_setup_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register SCM Setup and MSSP management tools."""

    # ── Folders ─────────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_folder_list(tenant_id: str = "", limit: int = 200) -> str:
        """List SCM folders (represents the tenant/customer hierarchy).

        Args:
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # Folder.list() has no real `limit` kwarg — slice client-side.
            results = client.folder.list()[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_folder_get(name: str, tenant_id: str = "") -> str:
        """Fetch a single SCM folder by name.

        Args:
            name: Folder name.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            obj = client.folder.fetch(name=name)
            return _fmt(obj)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── Devices ─────────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_device_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List devices (firewalls, Panorama) onboarded to SCM.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # Device.list() ignores `folder` (devices are tenant-global, not
            # folder-scoped) and has no real `limit` kwarg.
            results = client.device.list()[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── Snippets ─────────────────────────────────────────────────────────────

    @mcp.tool()
    def scm_snippet_list(tenant_id: str = "", limit: int = 200) -> str:
        """List configuration snippets available in SCM.

        Args:
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # Snippet.list() has no real `limit` kwarg — slice client-side.
            results = client.snippet.list()[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── MSSP Tenant Management ──────────────────────────────────────────────

    @mcp.tool()
    def mssp_list_tenants() -> str:
        """List all MSSP tenant IDs that currently have active SCM clients.

        Returns which tenants are loaded and ready without needing
        re-authentication.
        """
        tenants = list_loaded_tenants()
        if not tenants:
            return "No tenants currently loaded."
        return "\n".join(f"- {t}" for t in tenants)

    @mcp.tool()
    def mssp_evict_tenant(tenant_id: str) -> str:
        """Remove a tenant's cached SCM client (forces re-authentication on next use).

        Use this after rotating OAuth2 credentials for a customer tenant.

        Args:
            tenant_id: SCM tenant ID to evict.
        """
        removed = evict_tenant(tenant_id)
        if removed:
            logger.info("tenant_evicted", tenant_id=tenant_id)
            return f"Tenant '{tenant_id}' evicted; next request will re-authenticate."
        return f"Tenant '{tenant_id}' was not loaded."
