"""
MCP tools for Prisma SD-WAN.

Uses the prisma-sase SDK (same service-account credentials as SCM).
All tools gracefully degrade if prisma-sase is not installed or auth fails.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..auth.oauth import get_tenant_meta, list_loaded_tenants
from ..auth.sdwan import get_sdwan_client, safe_items
from ..utils.formatting import format_result as _fmt
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_sdwan_tools(mcp: FastMCP, get_scm_client_credentials: Any) -> None:
    """Register Prisma SD-WAN MCP tools."""

    def _sdwan(tenant_id: str = "") -> Any:
        """Resolve SD-WAN client using the cached TenantConfig for this tenant."""
        # Resolve tenant_id: use supplied value or fall back to first loaded tenant
        tid = tenant_id or (list_loaded_tenants() or [""])[0]
        tc = get_tenant_meta(tid)
        if tc is None:
            raise ValueError(
                f"Tenant {tid!r} is not loaded. Check settings.toml and restart the server."
            )
        return get_sdwan_client(tc)

    # ── Sites ─────────────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_sites(tenant_id: str = "", site_id: str = "") -> str:
        """List Prisma SD-WAN sites (branches, data centres, hub sites).

        Returns name, address, site type (branch/dc/hub), element count,
        admin state, and WAN interface count for each site.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Optional specific site ID to fetch.

        Returns:
            JSON array of site objects.
        """
        try:
            sdk = _sdwan(tenant_id)
            resp = sdk.get.sites(site_id=site_id or None)
            sites = safe_items(resp)
            summary = [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "description": s.get("description", ""),
                    "address": s.get("address", {}),
                    "element_cluster_role": s.get("element_cluster_role"),
                    "service_binding": s.get("service_binding"),
                    "admin_state": s.get("admin_state"),
                    "network_policysetstack_id": s.get("network_policysetstack_id"),
                    "priority_policysetstack_id": s.get("priority_policysetstack_id"),
                }
                for s in sites
            ]
            return _fmt({"total": len(summary), "sites": summary})
        except Exception as exc:
            return f"Error: {exc}"

    # ── Elements (ION devices) ────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_elements(
        tenant_id: str = "",
        site_id: str = "",
        element_id: str = "",
    ) -> str:
        """List Prisma SD-WAN ION elements (physical or virtual appliances).

        Returns model, serial, software version, site assignment, HA role,
        and connected state for each element.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Filter to a specific site ID.
            element_id: Fetch a specific element by ID.

        Returns:
            JSON array of element objects.
        """
        try:
            sdk = _sdwan(tenant_id)
            # Get.elements() only accepts `element_id` — it has no server-side
            # site_id filter, so fetch everything and filter client-side.
            resp = sdk.get.elements(element_id=element_id or None)
            elements = safe_items(resp)
            if site_id:
                elements = [e for e in elements if e.get("site_id") == site_id]
            summary = [
                {
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "site_id": e.get("site_id"),
                    "model_name": e.get("model_name"),
                    "serial_number": e.get("serial_number"),
                    "sw_version": e.get("sw_version"),
                    "hw_id": e.get("hw_id"),
                    "admin_state": e.get("admin_state"),
                    "connected": e.get("connected"),
                    "role": e.get("role"),
                    "cluster_insertion_mode": e.get("cluster_insertion_mode"),
                }
                for e in elements
            ]
            return _fmt({"total": len(summary), "elements": summary})
        except Exception as exc:
            return f"Error: {exc}"

    # ── WAN Interfaces ────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_wan_interfaces(
        tenant_id: str = "",
        site_id: str = "",
        element_id: str = "",
    ) -> str:
        """List Prisma SD-WAN WAN interfaces for a site or element.

        Returns interface name, type (public/private), circuit, bandwidth,
        network label, and link quality for each WAN interface.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Required — site ID to query.
            element_id: Optional — filter to a specific element.

        Returns:
            JSON array of WAN interface objects.
        """
        try:
            sdk = _sdwan(tenant_id)
            if not site_id:
                return "Error: site_id is required — use sdwan_list_sites to find site IDs"
            resp = sdk.get.waninterfaces(site_id=site_id)
            ifaces = safe_items(resp)
            if element_id:
                ifaces = [i for i in ifaces if i.get("element_id") == element_id]
            summary = [
                {
                    "id": i.get("id"),
                    "name": i.get("name"),
                    "type": i.get("type"),
                    "network_id": i.get("network_id"),
                    "label_id": i.get("label_id"),
                    "bwc_enabled": i.get("bwc_enabled"),
                    "link_bw_down": i.get("link_bw_down"),
                    "link_bw_up": i.get("link_bw_up"),
                    "lqm_enabled": i.get("lqm_enabled"),
                }
                for i in ifaces
            ]
            return _fmt({"site_id": site_id, "total": len(summary), "wan_interfaces": summary})
        except Exception as exc:
            return f"Error: {exc}"

    # ── WAN IP Summary ───────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_wan_ip_summary(tenant_id: str = "", site_id: str = "") -> str:
        """Report the live public/private WAN IP address bound to each ION element.

        For every element (or just those at `site_id` if given), inspects each
        interface marked used_for="public" or "private" in its config and reads
        the live-bound IP from the interface's operational status — this covers
        both static and DHCP-assigned WAN circuits, which the config object
        alone cannot show for DHCP.

        Use this to populate a WAN IP inventory table/diagram for AS-BUILT
        documentation, or to spot circuits that are down or missing an address.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Optional — limit to elements at this site.

        Returns:
            JSON array of {site_name, element_name, interface_name, used_for,
            operational_state, ipv4_addresses, ipv6_addresses} records.
        """
        try:
            from ..audit.extractor import extract_sdwan_wan_ips

            sdk = _sdwan(tenant_id)
            sites = safe_items(sdk.get.sites())
            elements = safe_items(sdk.get.elements())
            if site_id:
                sites = [s for s in sites if s.get("id") == site_id]
                elements = [e for e in elements if e.get("site_id") == site_id]

            wan_ips, errors = extract_sdwan_wan_ips(sdk, sites, elements)
            result: dict[str, Any] = {"total": len(wan_ips), "wan_ips": wan_ips}
            if errors:
                result["warnings"] = errors
            return _fmt(result)
        except Exception as exc:
            return f"Error: {exc}"

    # ── WAN Networks & Labels ─────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_wan_networks(tenant_id: str = "") -> str:
        """List Prisma SD-WAN WAN networks (ISP circuit definitions).

        Returns network name, type (publicwan/privatewan/lte), and provider info.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).

        Returns:
            JSON array of WAN network objects.
        """
        try:
            sdk = _sdwan(tenant_id)
            resp = sdk.get.wannetworks()
            networks = safe_items(resp)
            labels_resp = sdk.get.waninterfacelabels()
            labels = safe_items(labels_resp)
            return _fmt(
                {
                    "wan_networks": [
                        {
                            "id": n.get("id"),
                            "name": n.get("name"),
                            "type": n.get("type"),
                            "provider_as_n": n.get("provider_as_n"),
                        }
                        for n in networks
                    ],
                    "wan_labels": [
                        {
                            "id": lbl.get("id"),
                            "name": lbl.get("name"),
                            "description": lbl.get("description"),
                        }
                        for lbl in labels
                    ],
                }
            )
        except Exception as exc:
            return f"Error: {exc}"

    # ── Path Groups ───────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_path_groups(tenant_id: str = "") -> str:
        """List Prisma SD-WAN path groups (circuit groupings for policy selection).

        Args:
            tenant_id: SCM tenant ID (MSSP mode).

        Returns:
            JSON array of path group objects.
        """
        try:
            sdk = _sdwan(tenant_id)
            resp = sdk.get.pathgroups()
            groups = safe_items(resp)
            return _fmt(
                {
                    "total": len(groups),
                    "path_groups": [
                        {
                            "id": g.get("id"),
                            "name": g.get("name"),
                            "description": g.get("description"),
                            "paths": g.get("paths", []),
                        }
                        for g in groups
                    ],
                }
            )
        except Exception as exc:
            return f"Error: {exc}"

    # ── Policies ──────────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_policies(tenant_id: str = "", policy_type: str = "network") -> str:
        """List Prisma SD-WAN policy sets.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            policy_type: 'network' (path selection), 'priority' (QoS),
                         'security' (NGFW), or 'all'.

        Returns:
            JSON policy set summary.
        """
        try:
            sdk = _sdwan(tenant_id)
            result: dict[str, Any] = {}

            pt = policy_type.lower()
            if pt in ("network", "all"):
                resp = sdk.get.networkpolicysets()
                result["network_policy_sets"] = [
                    {
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "description": p.get("description"),
                        "defaultrule_policyset": p.get("defaultrule_policyset"),
                    }
                    for p in safe_items(resp)
                ]
            if pt in ("priority", "all"):
                resp = sdk.get.prioritypolicysets()
                result["priority_policy_sets"] = [
                    {"id": p.get("id"), "name": p.get("name"), "description": p.get("description")}
                    for p in safe_items(resp)
                ]
            if pt in ("security", "all"):
                resp = sdk.get.securitypolicysets()
                result["security_policy_sets"] = [
                    {"id": p.get("id"), "name": p.get("name"), "description": p.get("description")}
                    for p in safe_items(resp)
                ]

            return _fmt(result)
        except Exception as exc:
            return f"Error: {exc}"

    # ── Hub / Spoke Clusters ──────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_clusters(tenant_id: str = "") -> str:
        """List Prisma SD-WAN hub and spoke clusters (HA topology).

        Args:
            tenant_id: SCM tenant ID (MSSP mode).

        Returns:
            JSON summary of hub clusters and spoke clusters.
        """
        try:
            sdk = _sdwan(tenant_id)
            _sites = safe_items(sdk.get.sites())
            hubs: list[dict[str, Any]] = []
            spokes: list[dict[str, Any]] = []
            for _s in _sites:
                _sid = _s.get("id")
                if _sid:
                    hubs.extend(safe_items(sdk.get.hubclusters(_sid)))
                    spokes.extend(safe_items(sdk.get.spokeclusters(_sid)))
            return _fmt(
                {
                    "hub_clusters": [
                        {
                            "id": h.get("id"),
                            "name": h.get("name"),
                            "site_id": h.get("site_id"),
                            "members": h.get("members", []),
                        }
                        for h in hubs
                    ],
                    "spoke_clusters": [
                        {
                            "id": s.get("id"),
                            "name": s.get("name"),
                            "site_id": s.get("site_id"),
                            "members": s.get("members", []),
                        }
                        for s in spokes
                    ],
                }
            )
        except Exception as exc:
            return f"Error: {exc}"

    # ── BGP ───────────────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_bgp(tenant_id: str = "", site_id: str = "", element_id: str = "") -> str:
        """List Prisma SD-WAN BGP configurations and peer status.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Filter to a specific site.
            element_id: Filter to a specific element.

        Returns:
            JSON BGP configs and peer summary.
        """
        try:
            sdk = _sdwan(tenant_id)
            if site_id and element_id:
                configs_resp = sdk.get.bgpconfigs(site_id=site_id, element_id=element_id)
                peers_resp = sdk.get.bgppeers(site_id=site_id, element_id=element_id)
            else:
                configs_resp = sdk.get.bgpconfigs(site_id=site_id or None, element_id=None)
                peers_resp = sdk.get.bgppeers(site_id=site_id or None, element_id=None)

            configs = safe_items(configs_resp)
            peers = safe_items(peers_resp)
            return _fmt(
                {
                    "bgp_configs": [
                        {
                            "id": c.get("id"),
                            "site_id": c.get("site_id"),
                            "element_id": c.get("element_id"),
                            "local_as_num": c.get("local_as_num"),
                            "router_id": c.get("router_id"),
                            "holdtime": c.get("holdtime"),
                        }
                        for c in configs
                    ],
                    "bgp_peers": [
                        {
                            "id": p.get("id"),
                            "name": p.get("name"),
                            "peer_ip": p.get("peer_ip"),
                            "peer_as_num": p.get("peer_as_num"),
                            "site_id": p.get("site_id"),
                            "admin_state": p.get("admin_state"),
                        }
                        for p in peers
                    ],
                }
            )
        except Exception as exc:
            return f"Error: {exc}"

    # ── VPN Overlay Topology Diagram ─────────────────────────────────────────

    @mcp.tool()
    def sdwan_topology_diagram(tenant_id: str = "", save_to: str = "") -> str:
        """Generate a Mermaid VPN overlay topology diagram for Prisma SD-WAN.

        Queries the SD-WAN controller topology API (POST /sdwan/v3.6/api/topology)
        to retrieve actual VPN adjacency between sites, then fetches per-link
        health status. Outputs a Mermaid graph TB diagram showing:

          - Hub / DC sites and branch sites as subgraph nodes
          - WAN cloud networks (Internet, MPLS, LTE) as intermediate cloud nodes
          - VPN tunnel edges with circuit type and UP/DOWN/degraded status icons
            ✅ UP  ⚠️ degraded  ❌ down

        Suitable for embedding directly in GitHub Markdown, Confluence, or the
        Prisma SASE AS-BUILT (Section 4).

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            save_to: Optional file path to write the diagram to (e.g. topology.md).

        Returns:
            Mermaid diagram as a fenced code block string.
        """
        try:
            from ..audit.extractor import extract_sdwan_wan_ips
            from ..audit.sdwan_topo import build_topology, topology_to_mermaid
            from ..auth.sdwan import safe_items

            sdk = _sdwan(tenant_id)

            sites = safe_items(sdk.get.sites())
            wan_networks = safe_items(sdk.get.wannetworks())
            elements = safe_items(sdk.get.elements())

            # Collect WAN interfaces across all sites
            wan_ifaces: list[dict[str, Any]] = []
            for site in sites:
                sid = site.get("id")
                if sid:
                    resp = sdk.get.waninterfaces(site_id=sid)
                    wan_ifaces.extend(safe_items(resp))

            connections = build_topology(sdk, sites, wan_ifaces, wan_networks)
            wan_ips, _wan_ip_errors = extract_sdwan_wan_ips(sdk, sites, elements)
            diagram = topology_to_mermaid(connections, sites, wan_networks, wan_ips=wan_ips)

            if not diagram:
                return "No VPN topology data returned — check SD-WAN credentials and site configuration."

            output = f"```mermaid\n{diagram}\n```\n\n**{len(connections)} VPN connections** across {len(sites)} sites."

            if save_to:
                from pathlib import Path

                Path(save_to).write_text(output)
                return f"Topology diagram saved to: {save_to}\n\n{output}"

            return output
        except Exception as exc:
            return f"Error: {exc}"

    # ── Debug: raw topology endpoint ─────────────────────────────────────────

    @mcp.tool()
    def sdwan_debug_topology(tenant_id: str = "", site_id: str = "") -> str:
        """Return the raw JSON from POST /sdwan/v3.6/api/topology for one site.

        Used to inspect the actual API response structure so field names can
        be verified against what build_topology expects.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Site ID to query. If omitted, uses the first site found.

        Returns:
            Raw JSON response (first 8 KB) plus the VPN links query result.
        """
        try:
            sdk = _sdwan(tenant_id)
            sites = safe_items(sdk.get.sites())
            if not sites:
                return "No sites found"
            sid = site_id or str(sites[0].get("id", ""))
            site_name = next((s.get("name") for s in sites if str(s.get("id")) == sid), sid)

            # 1. Topology POST
            url = str(sdk.controller) + "/sdwan/v3.6/api/topology"
            payload = {"nodes": [sid]}
            resp = sdk._session.post(url, json=payload)  # noqa: SLF001
            topo_raw = (
                resp.json()
                if resp.status_code == 200
                else {"http_error": resp.status_code, "body": resp.text[:500]}
            )

            # 2. VPN links query (alternate endpoint)
            vpn_url = str(sdk.controller) + "/sdwan/v2.0/api/vpnlinks/query"
            vpn_resp = sdk._session.post(vpn_url, json={})  # noqa: SLF001
            vpn_raw = (
                vpn_resp.json()
                if vpn_resp.status_code == 200
                else {"http_error": vpn_resp.status_code, "body": vpn_resp.text[:500]}
            )

            return _fmt(
                {
                    "site_queried": {"id": sid, "name": site_name},
                    "topology_endpoint": url,
                    "topology_payload": payload,
                    "topology_response_keys": list(topo_raw.keys())
                    if isinstance(topo_raw, dict)
                    else type(topo_raw).__name__,
                    "topology_response": topo_raw,
                    "vpnlinks_query_keys": list(vpn_raw.keys())
                    if isinstance(vpn_raw, dict)
                    else type(vpn_raw).__name__,
                    "vpnlinks_sample": vpn_raw
                    if not isinstance(vpn_raw, dict)
                    else {k: v[:3] if isinstance(v, list) else v for k, v in vpn_raw.items()},
                }
            )[:8000]
        except Exception as exc:
            import traceback

            return f"Error: {exc}\n{traceback.format_exc()}"

    # ── Topology Summary ──────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_topology(tenant_id: str = "") -> str:
        """Generate a full Prisma SD-WAN topology summary.

        Pulls sites, elements, WAN networks, hub/spoke clusters, and policy
        sets to produce a single structured overview of the SD-WAN deployment.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).

        Returns:
            JSON topology summary with site and element inventory.
        """
        try:
            sdk = _sdwan(tenant_id)

            sites = safe_items(sdk.get.sites())
            elements = safe_items(sdk.get.elements())
            networks = safe_items(sdk.get.wannetworks())
            labels = safe_items(sdk.get.waninterfacelabels())
            hubs: list[dict[str, Any]] = []
            spokes: list[dict[str, Any]] = []
            for _s in sites:
                _sid = _s.get("id")
                if _sid:
                    hubs.extend(safe_items(sdk.get.hubclusters(_sid)))
                    spokes.extend(safe_items(sdk.get.spokeclusters(_sid)))
            net_policies = safe_items(sdk.get.networkpolicysets())
            pri_policies = safe_items(sdk.get.prioritypolicysets())

            # Build site → elements map
            elem_by_site: dict[str, list[dict[str, Any]]] = {}
            for e in elements:
                sid = e.get("site_id", "unassigned")
                elem_by_site.setdefault(sid, []).append(
                    {
                        "id": e.get("id"),
                        "name": e.get("name"),
                        "model": e.get("model_name"),
                        "serial": e.get("serial_number"),
                        "sw_version": e.get("sw_version"),
                        "connected": e.get("connected"),
                        "role": e.get("role"),
                    }
                )

            site_inventory = [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "role": s.get("element_cluster_role"),
                    # address may be explicitly null (not just absent), so `or {}`
                    # guards against 'NoneType' object has no attribute 'get'.
                    "address": (s.get("address") or {}).get("city", "")
                    + ", "
                    + (s.get("address") or {}).get("country", ""),
                    "elements": elem_by_site.get(s.get("id", ""), []),
                }
                for s in sites
            ]

            return _fmt(
                {
                    "summary": {
                        "total_sites": len(sites),
                        "total_elements": len(elements),
                        "total_wan_networks": len(networks),
                        "hub_clusters": len(hubs),
                        "spoke_clusters": len(spokes),
                        "network_policy_sets": len(net_policies),
                        "priority_policy_sets": len(pri_policies),
                    },
                    "wan_networks": [
                        {"name": n.get("name"), "type": n.get("type")} for n in networks
                    ],
                    "wan_labels": [{"name": lbl.get("name")} for lbl in labels],
                    "sites": site_inventory,
                }
            )
        except Exception as exc:
            return f"Error: {exc}"
