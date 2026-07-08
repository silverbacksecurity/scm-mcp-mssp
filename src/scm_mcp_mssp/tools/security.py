"""
MCP tools for SCM Security Services resources.

Covers: security rules, anti-spyware profiles, URL filtering profiles,
        vulnerability protection, DNS security, decryption profiles,
        wildfire analysis.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..utils.errors import handle_scm_exception
from ..utils.formatting import format_result as _fmt
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_security_tools(mcp: FastMCP, get_client: Any) -> None:
    """Register all SCM Security tools onto the MCP server."""

    # ── Security Rules ──────────────────────────────────────────────────────

    @mcp.tool()
    def scm_security_rule_list(
        folder: str,
        tenant_id: str = "",
        limit: int = 200,
        position: str = "pre",
    ) -> str:
        """List security policy rules in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum number of results.
            position: Rule position — 'pre' or 'post'.
        """
        try:
            client = get_client(tenant_id)
            # SecurityRule.list() has no real `limit` kwarg (silently swallowed into
            # **filters); its rulebase-selector kwarg is `rulebase`, not `position`.
            results = client.security_rule.list(folder=folder, rulebase=position)[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_security_rule_get(name: str, folder: str, tenant_id: str = "") -> str:
        """Fetch a single security rule by name.

        Args:
            name: Rule name.
            folder: SCM folder.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            obj = client.security_rule.fetch(name=name, folder=folder)
            return _fmt(obj)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_security_rule_create(
        name: str,
        folder: str,
        action: str,
        source_zones: list[str],
        destination_zones: list[str],
        source_addresses: list[str] | None = None,
        destination_addresses: list[str] | None = None,
        applications: list[str] | None = None,
        services: list[str] | None = None,
        profile_setting: dict[str, Any] | None = None,
        description: str = "",
        disabled: bool = False,
        tenant_id: str = "",
    ) -> str:
        """Create a security policy rule.

        Args:
            name: Rule name.
            folder: SCM folder.
            action: 'allow' or 'deny'.
            source_zones: Source security zones.
            destination_zones: Destination security zones.
            source_addresses: Source addresses/groups (default: ['any']).
            destination_addresses: Destination addresses/groups (default: ['any']).
            applications: Application names (default: ['any']).
            services: Services (default: ['application-default']).
            profile_setting: Security profile group dict.
            description: Optional description.
            disabled: Whether the rule is disabled.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            payload: dict[str, Any] = {
                "name": name,
                "folder": folder,
                "action": action,
                "from": source_zones,
                "to": destination_zones,
                "source": source_addresses or ["any"],
                "destination": destination_addresses or ["any"],
                "application": applications or ["any"],
                "service": services or ["application-default"],
                "disabled": disabled,
            }
            if description:
                payload["description"] = description
            if profile_setting:
                payload["profile_setting"] = profile_setting
            obj = client.security_rule.create(payload)
            logger.info("security_rule_created", name=name, folder=folder, action=action)
            return _fmt(obj)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_security_rule_delete(name: str, folder: str, tenant_id: str = "") -> str:
        """Delete a security rule by name.

        Args:
            name: Rule name.
            folder: SCM folder.
            tenant_id: SCM tenant ID.
        """
        try:
            client = get_client(tenant_id)
            obj = client.security_rule.fetch(name=name, folder=folder)
            client.security_rule.delete(obj.id)
            logger.info("security_rule_deleted", name=name, folder=folder)
            return f"Deleted security rule '{name}' from folder '{folder}'"
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    # ── Security Profiles ───────────────────────────────────────────────────

    @mcp.tool()
    def scm_anti_spyware_profile_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List anti-spyware profiles in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # AntiSpywareProfile.list() has no real `limit` kwarg — slice client-side.
            results = client.anti_spyware_profile.list(folder=folder)[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"

    @mcp.tool()
    def scm_url_category_list(folder: str, tenant_id: str = "", limit: int = 200) -> str:
        """List URL filtering categories in a SCM folder.

        Args:
            folder: SCM folder.
            tenant_id: SCM tenant ID.
            limit: Maximum results.
        """
        try:
            client = get_client(tenant_id)
            # URLCategories.list() has no real `limit` kwarg — slice client-side.
            results = client.url_category.list(folder=folder)[: max(0, limit)]
            return _fmt(results)
        except Exception as exc:
            return f"Error: {handle_scm_exception(exc)}"
