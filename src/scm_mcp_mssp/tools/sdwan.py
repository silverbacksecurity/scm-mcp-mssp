"""
MCP tools for Prisma SD-WAN.

Uses the prisma-sase SDK (same service-account credentials as SCM).
All tools gracefully degrade if prisma-sase is not installed or auth fails.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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

    def _iso(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def _window(hours: int) -> tuple[str, str]:
        now = datetime.now(UTC)
        return _iso(now - timedelta(hours=hours)), _iso(now)

    def _api_error(label: str, resp: Any) -> str:
        """Render a prisma-sase error response as a readable message."""
        code = getattr(resp, "status_code", "?")
        body = (getattr(resp, "text", "") or "")[:300]
        if code == 403:
            return (
                f"{label}: HTTP 403 — the service account's role does not include "
                "this permission (same RBAC class as the known allocated_ips 403; "
                "needs a broader read role, e.g. Insights/monitor read)."
            )
        return f"{label}: HTTP {code} {body}".rstrip()

    def _name_maps(sdk: Any) -> tuple[dict[str, str], dict[str, str]]:
        """Return {site_id: name} and {element_id: name} lookup maps."""
        site_names = {s.get("id"): s.get("name", s.get("id")) for s in safe_items(sdk.get.sites())}
        elem_names = {
            e.get("id"): e.get("name") or e.get("id") for e in safe_items(sdk.get.elements())
        }
        return site_names, elem_names

    # ── Sites ─────────────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_list_sites(tenant_id: str = "", site_id: str = "") -> str:
        """List Prisma SD-WAN sites (branches, data centres, hub sites).

        Returns name, address, geo location (latitude/longitude), site type
        (branch/dc/hub), element count, admin state, and WAN interface count
        for each site.

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
                    "location": s.get("location", {}),
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
                    # the elements API names this field software_version
                    "sw_version": e.get("software_version") or e.get("sw_version"),
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
    def sdwan_wan_ip_summary(
        tenant_id: str = "",
        site_id: str = "",
        enrich: bool = False,
    ) -> str:
        """Report the live public/private WAN IP address bound to each ION element.

        For every element (or just those at `site_id` if given), inspects each
        interface marked used_for="public" or "private" in its config and reads
        the live-bound IP from the interface's operational status — this covers
        both static and DHCP-assigned WAN circuits, which the config object
        alone cannot show for DHCP. Each record carries the site's configured
        street address and geo location (latitude/longitude).

        Also reports each element's **detected public IP** (`detected_public_ips`
        section): the post-NAT source address the cloud controller sees the
        ION's config/events connection arriving from (element status
        `config_and_events_from`). For branches whose WAN interface holds an
        RFC1918 address behind an upstream NAT, this is the real public egress
        IP — no on-device lookup needed. Caveat: it reflects the circuit the
        controller connection rides (normally the primary internet circuit),
        so a multi-WAN branch shows one NAT IP, not one per circuit.

        With enrich=true, each public WAN IP and detected public IP is
        additionally looked up against an external IP-intelligence provider
        (whatsmyip-style reverse lookup: ISP, organisation, ASN, reverse DNS,
        and IP geolocation) so circuit provider and location can be verified
        against what is configured. Note this sends the tenant's public IPs
        to a third-party service (`ip_enrichment_provider` in settings,
        default ip-api.com) — hence opt-in, never on by default.

        Use this to populate a WAN IP inventory table/diagram for AS-BUILT
        documentation, or to spot circuits that are down or missing an address.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Optional — limit to elements at this site.
            enrich: Look up ISP/ASN/rDNS/geo for each public WAN IP.

        Returns:
            JSON with `wan_ips` records ({site_name, site_address, site_location,
            element_name, interface_name, used_for, operational_state,
            ipv4_addresses, ipv6_addresses[, enrichment]}) and
            `detected_public_ips` ({site_name, element_name, detected_public_ip,
            connected[, enrichment]}).
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

            site_geo = {
                s.get("id"): {
                    "address": s.get("address") or {},
                    "location": s.get("location") or {},
                }
                for s in sites
                if s.get("id")
            }
            for rec in wan_ips:
                geo = site_geo.get(rec.get("site_id"), {})
                rec["site_address"] = geo.get("address", {})
                rec["site_location"] = geo.get("location", {})

            # Post-NAT public IP per element, as seen by the cloud controller
            # (element status `config_and_events_from`). The only API-visible
            # source when the WAN interface itself holds an RFC1918 address
            # behind upstream NAT — there is no remote-exec on IONs.
            site_by_id = {s.get("id"): s for s in sites if s.get("id")}
            detected: list[dict[str, Any]] = []
            for elem in elements:
                eid = elem.get("id")
                if not eid:
                    continue
                try:
                    status_items = safe_items(sdk.get.element_status(element_id=eid))
                except Exception as exc:
                    errors.append(f"sdwan_element_status[{eid}]: {exc}")
                    continue
                status = status_items[0] if status_items else {}
                public_ip = status.get("config_and_events_from") or ""
                # SD-WAN parks unclaimed/unassigned elements under site_id "1"
                elem_site_id = elem.get("site_id")
                site_name = (
                    "(unassigned)"
                    if elem_site_id == "1"
                    else site_by_id.get(elem_site_id, {}).get("name", elem_site_id)
                )
                detected.append(
                    {
                        "site_id": elem_site_id,
                        "site_name": site_name,
                        "element_id": eid,
                        "element_name": elem.get("name", eid),
                        "connected": elem.get("connected"),
                        "detected_public_ip": public_ip,
                    }
                )

            if enrich:
                from ..utils.ipenrich import enrich_public_ips, global_ips

                candidates = [
                    ip
                    for rec in wan_ips
                    for ip in (rec.get("ipv4_addresses") or []) + (rec.get("ipv6_addresses") or [])
                ] + [d["detected_public_ip"] for d in detected]
                by_ip, enrich_warnings = enrich_public_ips(candidates)
                for rec in wan_ips:
                    matches = [
                        by_ip[ip]
                        for ip in global_ips(
                            (rec.get("ipv4_addresses") or []) + (rec.get("ipv6_addresses") or [])
                        )
                        if ip in by_ip
                    ]
                    if matches:
                        rec["enrichment"] = matches
                for d in detected:
                    hits = global_ips([d["detected_public_ip"]])
                    if hits and hits[0] in by_ip:
                        d["enrichment"] = by_ip[hits[0]]
                errors = errors + [f"enrichment: {w}" for w in enrich_warnings]

            result: dict[str, Any] = {
                "total": len(wan_ips),
                "wan_ips": wan_ips,
                "detected_public_ips": detected,
            }
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
                        "sw_version": e.get("software_version") or e.get("sw_version"),
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

    # ── Events / Alarms ───────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_events(
        tenant_id: str = "",
        hours: int = 24,
        category: str = "all",
        severity: str = "",
        site_id: str = "",
        code: str = "",
        include_cleared: bool = True,
        max_events: int = 50,
    ) -> str:
        """List Prisma SD-WAN events (alarms and alerts) with a severity summary.

        Queries the controller event feed (POST events/query) for the last
        `hours` hours, newest first. Each event carries its event code,
        human-readable display name and category (resolved from the tenant's
        event-code catalog), severity, priority, cleared/acknowledged/standing
        state, and the site and element it fired on.

        The `summary` section counts events by severity and by code, and
        highlights how many are still active (not cleared) — a quick NOC
        health read without paging through the raw feed.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            hours: Look-back window in hours (default 24).
            category: 'alarm', 'alert', or 'all'.
            severity: Comma-separated filter, e.g. 'critical,major'.
            site_id: Limit to events at this site.
            code: Comma-separated event-code filter,
                  e.g. 'DEVICEHW_INTERFACE_DOWN'.
            include_cleared: Include events that have already cleared
                             (set False for active-issues-only).
            max_events: Maximum events to return (default 50).

        Returns:
            JSON with `summary` (counts by severity/code, active count) and
            `events` (trimmed records, newest first).
        """
        try:
            sdk = _sdwan(tenant_id)
            start_time, end_time = _window(hours)

            query: dict[str, Any] = {}
            cat = category.lower()
            query["type"] = ["alarm", "alert"] if cat == "all" else [cat]
            if site_id:
                query["site"] = [site_id]
            if code:
                query["code"] = [c.strip() for c in code.split(",") if c.strip()]

            payload: dict[str, Any] = {
                "limit": {
                    "count": max(max_events, 1),
                    "sort_on": "time",
                    "sort_order": "descending",
                },
                "view": {"summary": False},
                "severity": [s.strip() for s in severity.split(",") if s.strip()],
                "query": query,
                "start_time": start_time,
                "end_time": end_time,
            }
            resp = sdk.post.events_query(payload)
            if not getattr(resp, "sdk_status", False):
                return f"Error: {_api_error('events_query', resp)}"
            content = getattr(resp, "sdk_content", {}) or {}
            events = list(content.get("items", []))
            total_count = content.get("total_count")

            if not include_cleared:
                events = [e for e in events if not e.get("cleared")]

            # Resolve event codes to display names and site/element IDs to names
            code_meta = {
                c.get("code"): c for c in safe_items(sdk.get.eventcodes()) if c.get("code")
            }
            site_names, elem_names = _name_maps(sdk)

            by_severity: dict[str, int] = {}
            by_code: dict[str, int] = {}
            active = 0
            trimmed: list[dict[str, Any]] = []
            for e in events:
                sev = e.get("severity", "unknown")
                by_severity[sev] = by_severity.get(sev, 0) + 1
                ecode = e.get("code", "unknown")
                by_code[ecode] = by_code.get(ecode, 0) + 1
                if not e.get("cleared"):
                    active += 1
                meta = code_meta.get(ecode, {})
                trimmed.append(
                    {
                        "id": e.get("id"),
                        "time": e.get("time"),
                        "code": ecode,
                        "display_name": meta.get("display_name", ecode),
                        "event_category": meta.get("category"),
                        "type": e.get("type"),
                        "severity": sev,
                        "priority": e.get("priority"),
                        "cleared": e.get("cleared"),
                        "acknowledged": e.get("acknowledged"),
                        "standing": e.get("standing"),
                        "site_name": site_names.get(e.get("site_id"), e.get("site_id")),
                        "element_name": elem_names.get(e.get("element_id"), e.get("element_id")),
                        "entity_ref": e.get("entity_ref"),
                        "info": e.get("info"),
                        "correlation_id": e.get("correlation_id"),
                    }
                )

            return _fmt(
                {
                    "window_hours": hours,
                    "summary": {
                        "returned": len(trimmed),
                        "total_in_window": total_count,
                        "active_not_cleared": active,
                        "by_severity": by_severity,
                        "by_code": dict(
                            sorted(by_code.items(), key=lambda kv: kv[1], reverse=True)
                        ),
                    },
                    "events": trimmed,
                }
            )
        except Exception as exc:
            return f"Error: {exc}"

    # ── Audit Log ─────────────────────────────────────────────────────────────

    @mcp.tool()
    def sdwan_audit_logs(tenant_id: str = "", hours: int = 24, limit: int = 50) -> str:
        """List Prisma SD-WAN audit-log entries (who changed what, and when).

        Queries the controller audit log (POST auditlog/query) for the last
        `hours` hours, newest first. Each entry records the operator, the
        request (method + resource URI), and the response code — the trail
        for config-change forensics and compliance evidence.

        Note: requires an audit-log read permission on the service account;
        view-only roles typically get HTTP 403 (reported gracefully).

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            hours: Look-back window in hours (default 24).
            limit: Maximum entries to return (default 50).

        Returns:
            JSON array of audit entries, or a clear RBAC message on 403.
        """
        try:
            sdk = _sdwan(tenant_id)
            since_ms = int((datetime.now(UTC) - timedelta(hours=hours)).timestamp() * 1000)
            payload = {
                "limit": limit,
                "query_params": {"request_ts": {"gte": since_ms}},
                "sort_params": {"request_ts": "desc"},
            }
            resp = sdk.post.query_auditlog(payload)
            if not getattr(resp, "sdk_status", False):
                return f"Error: {_api_error('auditlog_query', resp)}"
            entries = list((getattr(resp, "sdk_content", {}) or {}).get("items", []))

            preferred = (
                "operator_email",
                "operator_id",
                "request_ts",
                "request_type",
                "request_uri",
                "resource_uri",
                "request_method",
                "response_code",
                "source_ip",
                "session_key_c",
                "id",
            )
            trimmed = [
                {k: e[k] for k in preferred if k in e} or e  # fall back to full record
                for e in entries
            ]
            return _fmt({"window_hours": hours, "total": len(trimmed), "audit_logs": trimmed})
        except Exception as exc:
            return f"Error: {exc}"

    # ── Software / Upgrade Status ─────────────────────────────────────────────

    @mcp.tool()
    def sdwan_software_status(tenant_id: str = "", element_id: str = "") -> str:
        """Report ION software versions, pending upgrades, and upgrade jobs.

        For each element (or just `element_id`): the running software version,
        the machine inventory record it maps to (model, serial, claim state),
        and the element's software status — active vs staged upgrade image,
        download progress, upgrade state, rollback version, and any scheduled
        download/upgrade window. Also lists in-flight upgrade jobs
        (upgrade_status query) and a version histogram across the estate,
        so version drift is visible at a glance.

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            element_id: Limit to a specific element.

        Returns:
            JSON with `version_histogram`, `elements` (per-element software
            state), `machines_unclaimed`, and `upgrade_jobs`.
        """
        try:
            sdk = _sdwan(tenant_id)
            elements = safe_items(sdk.get.elements())
            if element_id:
                elements = [e for e in elements if e.get("id") == element_id]
            site_names, _ = _name_maps(sdk)

            machines = safe_items(sdk.get.machines())
            machine_by_element = {
                m.get("em_element_id"): m for m in machines if m.get("em_element_id")
            }

            warnings: list[str] = []
            records: list[dict[str, Any]] = []
            histogram: dict[str, int] = {}
            for e in elements:
                eid = e.get("id")
                ver = e.get("software_version") or e.get("sw_version") or "unknown"
                histogram[ver] = histogram.get(ver, 0) + 1
                rec: dict[str, Any] = {
                    "element_id": eid,
                    "element_name": e.get("name") or eid,
                    "site_name": site_names.get(e.get("site_id"), e.get("site_id")),
                    "model": e.get("model_name"),
                    "serial": e.get("serial_number"),
                    "connected": e.get("connected"),
                    "sw_version": ver,
                }
                m = machine_by_element.get(eid)
                if m:
                    rec["machine_state"] = m.get("machine_state")
                    rec["image_version"] = m.get("image_version")
                try:
                    statuses = safe_items(sdk.get.software_status(eid))
                except Exception as exc:  # per-element degrade, keep the sweep going
                    warnings.append(f"software_status[{eid}]: {exc}")
                    statuses = []
                if statuses:
                    s = max(statuses, key=lambda x: x.get("_updated_on_utc") or 0)
                    rec["software_status"] = {
                        "active_version": s.get("active_version"),
                        "upgrade_pending": bool(
                            s.get("upgrade_image_id")
                            and s.get("upgrade_image_id") != s.get("active_image_id")
                        ),
                        "upgrade_state": s.get("upgrade_state"),
                        "download_percent": s.get("download_percent"),
                        "rollback_version": s.get("rollback_version"),
                        "failure_info": s.get("failure_info"),
                        "scheduled_download": s.get("scheduled_download"),
                        "scheduled_upgrade": s.get("scheduled_upgrade"),
                    }
                records.append(rec)

            unclaimed = [
                {
                    "machine_id": m.get("id"),
                    "serial": m.get("sl_no"),
                    "model": m.get("model_name"),
                    "machine_state": m.get("machine_state"),
                    "image_version": m.get("image_version"),
                    "connected": m.get("connected"),
                }
                for m in machines
                if m.get("machine_state") != "claimed"
            ]

            jobs_resp = sdk.post.query_upgrade_status({"limit": 25})
            if getattr(jobs_resp, "sdk_status", False):
                jobs = list((getattr(jobs_resp, "sdk_content", {}) or {}).get("items", []))
            else:
                jobs = []
                warnings.append(_api_error("upgrade_status_query", jobs_resp))

            result: dict[str, Any] = {
                "total_elements": len(records),
                "version_histogram": histogram,
                "elements": records,
                "machines_unclaimed": unclaimed,
                "upgrade_jobs": jobs,
            }
            if warnings:
                result["warnings"] = warnings
            return _fmt(result)
        except Exception as exc:
            return f"Error: {exc}"

    # ── Policy Rules (path / QoS / NAT / security) ────────────────────────────

    @mcp.tool()
    def sdwan_policy_rules(
        tenant_id: str = "",
        policy_type: str = "path",
        policy_set_id: str = "",
    ) -> str:
        """List Prisma SD-WAN policy sets, stacks, and the rules inside them.

        Complements sdwan_list_policies (set names only) with the actual rule
        contents — what traffic each rule matches and what it does:

          - 'path'     — network policy: which WAN paths an app may use
                         (active/backup path labels, service context)
          - 'qos'      — priority policy: priority level and DSCP per app
          - 'nat'      — NAT policy: source/destination NAT actions, zones,
                         pools, ports
          - 'security' — NGFW security policy: zone-to-zone allow/deny rules,
                         apps, prefixes, security-profile group
          - 'security_legacy' — original (pre-NGFW) security policy rules

        Rules for every set are fetched when the tenant has ≤8 sets of that
        type; otherwise pass `policy_set_id` to pick one (set list is always
        returned, so the IDs are one call away).

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            policy_type: 'path', 'qos', 'nat', 'security', or 'security_legacy'.
            policy_set_id: Fetch rules for this specific policy set only.

        Returns:
            JSON with `policy_sets`, `policy_set_stacks`, and `rules_by_set`.
        """
        try:
            sdk = _sdwan(tenant_id)
            pt = policy_type.lower()

            registry: dict[str, tuple[str, str, str | None]] = {
                "path": ("networkpolicysets", "networkpolicyrules", "networkpolicysetstacks"),
                "qos": ("prioritypolicysets", "prioritypolicyrules", "prioritypolicysetstacks"),
                "nat": ("natpolicysets", "natpolicyrules", "natpolicysetstacks"),
                "security": (
                    "ngfwsecuritypolicysets",
                    "ngfwsecuritypolicyrules",
                    "ngfwsecuritypolicysetstacks",
                ),
                "security_legacy": ("securitypolicysets", "securitypolicyrules", None),
            }
            if pt not in registry:
                return f"Error: unknown policy_type {policy_type!r} — use one of {sorted(registry)}"
            sets_name, rules_name, stacks_name = registry[pt]
            api: dict[str, Any] = {
                "sets": getattr(sdk.get, sets_name),
                "rules": getattr(sdk.get, rules_name),
                "stacks": getattr(sdk.get, stacks_name) if stacks_name else None,
            }

            psets = safe_items(api["sets"]())
            set_summaries = [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "default": p.get("defaultrule_policyset", p.get("default_policysetstack")),
                }
                for p in psets
            ]

            stacks: list[dict[str, Any]] = []
            if api["stacks"] is not None:
                stacks = [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "policyset_ids": s.get("policyset_ids", []),
                        "default": s.get("default_policysetstack"),
                    }
                    for s in safe_items(api["stacks"]())
                ]

            warnings: list[str] = []
            rules_by_set: dict[str, list[dict[str, Any]]] = {}
            note = ""
            if policy_set_id:
                targets = [p for p in psets if p.get("id") == policy_set_id]
                if not targets:
                    return f"Error: policy set {policy_set_id!r} not found in {pt} sets"
            elif len(psets) <= 8:
                targets = psets
            else:
                targets = []
                note = (
                    f"{len(psets)} {pt} policy sets — pass policy_set_id to fetch "
                    "rules for one of them."
                )

            rule_trimmers: dict[str, Any] = {
                "path": lambda r: {
                    "name": r.get("name"),
                    "order": r.get("order_number"),
                    "enabled": r.get("enabled"),
                    "app_def_ids": r.get("app_def_ids"),
                    "paths_allowed": r.get("paths_allowed"),
                    "service_context": r.get("service_context"),
                },
                "qos": lambda r: {
                    "name": r.get("name"),
                    "order": r.get("order_number"),
                    "enabled": r.get("enabled"),
                    "priority_number": r.get("priority_number"),
                    "dscp": r.get("dscp"),
                    "app_def_ids": r.get("app_def_ids"),
                },
                "nat": lambda r: {
                    "name": r.get("name"),
                    "enabled": r.get("enabled"),
                    "protocol": r.get("protocol"),
                    "actions": r.get("actions"),
                    "source_zone_id": r.get("source_zone_id"),
                    "destination_zone_id": r.get("destination_zone_id"),
                    "source_prefixes_id": r.get("source_prefixes_id"),
                    "destination_prefixes_id": r.get("destination_prefixes_id"),
                    "source_ports": r.get("source_ports"),
                    "destination_ports": r.get("destination_ports"),
                },
                "security": lambda r: {
                    "name": r.get("name"),
                    "action": r.get("action"),
                    "enabled": r.get("enabled"),
                    "app_def_ids": r.get("app_def_ids"),
                    "source_zone_ids": r.get("source_zone_ids"),
                    "destination_zone_ids": r.get("destination_zone_ids"),
                    "source_prefix_ids": r.get("source_prefix_ids"),
                    "destination_prefix_ids": r.get("destination_prefix_ids"),
                    "services": r.get("services"),
                    "security_profile_group_id": r.get("security_profile_group_id"),
                },
                "security_legacy": lambda r: {
                    "name": r.get("name"),
                    "action": r.get("action"),
                    "enabled": r.get("enabled"),
                    "application_ids": r.get("application_ids"),
                    "source_filter_ids": r.get("source_filter_ids"),
                    "destination_filter_ids": r.get("destination_filter_ids"),
                },
            }
            trim = rule_trimmers[pt]
            for p in targets:
                sid = p.get("id")
                if not sid:
                    continue
                try:
                    rules_by_set[p.get("name") or sid] = [
                        {"id": r.get("id"), **trim(r)} for r in safe_items(api["rules"](sid))
                    ]
                except Exception as exc:
                    warnings.append(f"rules[{sid}]: {exc}")

            result: dict[str, Any] = {
                "policy_type": pt,
                "total_sets": len(psets),
                "policy_sets": set_summaries,
                "policy_set_stacks": stacks,
                "rules_by_set": rules_by_set,
            }
            if note:
                result["note"] = note
            if warnings:
                result["warnings"] = warnings
            return _fmt(result)
        except Exception as exc:
            return f"Error: {exc}"

    # ── Link Health / Performance ─────────────────────────────────────────────

    @mcp.tool()
    def sdwan_link_health(
        tenant_id: str = "",
        site_id: str = "",
        hours: int = 3,
        interval: str = "5min",
        include_bandwidth: bool = True,
        max_paths: int = 6,
    ) -> str:
        """Report link quality (latency, jitter, MOS) and bandwidth for a site.

        Lists every VPN overlay path (anynet link) touching the site with its
        admin state and endpoints, then queries the monitor API for link
        quality metrics per path over the last `hours` hours — LqmLatency and
        LqmJitter in milliseconds plus LqmMos voice quality score — and, with
        include_bandwidth, site-level ingress/egress BandwidthUsage in Mbps.
        Datapoints are reduced to min/avg/max per series so the answer stays
        readable; empty series mean LQM probing is disabled or the path was
        idle in the window.

        The monitor API accepts only one path per LQM request, so admin-up
        paths are queried first, capped at `max_paths` (raise it to cover
        more paths at the cost of extra API calls).

        Args:
            tenant_id: SCM tenant ID (MSSP mode).
            site_id: Required — site to report on (see sdwan_list_sites).
            hours: Look-back window in hours (default 3).
            interval: Datapoint interval: '5min', '1hour', or '1day'.
            include_bandwidth: Also query site-level bandwidth usage.
            max_paths: Cap on paths queried for LQM (default 6).

        Returns:
            JSON with `paths` (anynet links at the site), `link_quality`
            (min/avg/max per metric per path), and `bandwidth` (site-level).
        """
        try:
            if not site_id:
                return "Error: site_id is required — use sdwan_list_sites to find site IDs"
            sdk = _sdwan(tenant_id)
            start_time, end_time = _window(hours)
            site_names, _ = _name_maps(sdk)

            links_resp = sdk.post.anynetlinks_query({"limit": 256})
            if not getattr(links_resp, "sdk_status", False):
                return f"Error: {_api_error('anynetlinks_query', links_resp)}"
            links = [
                lnk
                for lnk in (getattr(links_resp, "sdk_content", {}) or {}).get("items", [])
                if site_id in (lnk.get("ep1_site_id"), lnk.get("ep2_site_id"))
            ]
            paths: list[dict[str, Any]] = []
            for lnk in links:
                remote_id = (
                    lnk.get("ep2_site_id")
                    if lnk.get("ep1_site_id") == site_id
                    else lnk.get("ep1_site_id")
                )
                paths.append(
                    {
                        "path_id": lnk.get("id"),
                        "name": lnk.get("name"),
                        "type": lnk.get("type"),
                        "admin_up": lnk.get("admin_up"),
                        "ep1_site": site_names.get(lnk.get("ep1_site_id"), lnk.get("ep1_site_id")),
                        "ep2_site": site_names.get(lnk.get("ep2_site_id"), lnk.get("ep2_site_id")),
                        "remote_site": site_names.get(remote_id, remote_id),
                    }
                )

            def _reduce(resp: Any, extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
                """Collapse monitor-API series into min/avg/max summaries."""
                out: list[dict[str, Any]] = []
                for metric in (resp.json() or {}).get("metrics", []):
                    for series in metric.get("series", []):
                        for data in series.get("data", []):
                            values = [
                                dp.get("value")
                                for dp in data.get("datapoints", [])
                                if dp.get("value") is not None
                            ]
                            out.append(
                                {
                                    **(extra or {}),
                                    "metric": series.get("name"),
                                    "unit": series.get("unit"),
                                    "view": series.get("view"),
                                    "datapoints": len(data.get("datapoints", [])),
                                    "min": min(values) if values else None,
                                    "avg": round(sum(values) / len(values), 2) if values else None,
                                    "max": max(values) if values else None,
                                }
                            )
                return out

            warnings: list[str] = []
            link_quality: list[dict[str, Any]] = []
            # LQM requests take exactly one path, and latency (round-trip)
            # rejects the direction view that jitter requires — so each path
            # needs two monitor calls. Query admin-up paths first.
            lqm_targets = sorted(paths, key=lambda p: not p.get("admin_up"))[:max_paths]
            base = {"start_time": start_time, "end_time": end_time, "interval": interval}
            # LqmMos only supports unit "count"; LqmPacketLoss is rejected
            # with METRIC_UNIT_NOT_SUPPORTED for every documented unit, so
            # it is deliberately absent here.
            lqm_calls = [
                # round-trip latency rejects the direction view the
                # directional metrics (jitter, MOS) require — two calls
                (
                    {},
                    [{"name": "LqmLatency", "statistics": ["average"], "unit": "milliseconds"}],
                ),
                (
                    {"individual": "direction"},
                    [
                        {"name": "LqmJitter", "statistics": ["average"], "unit": "milliseconds"},
                        {"name": "LqmMos", "statistics": ["average"], "unit": "count"},
                    ],
                ),
            ]
            for p in lqm_targets:
                pid = p["path_id"]
                tag = {"path_id": pid, "remote_site": p["remote_site"]}
                for view, metrics in lqm_calls:
                    lqm_resp = sdk.post.monitor_metrics(
                        {
                            **base,
                            "metrics": metrics,
                            "view": view,
                            "filter": {"site": [site_id], "path": [pid]},
                        }
                    )
                    if getattr(lqm_resp, "sdk_status", False):
                        link_quality.extend(_reduce(lqm_resp, extra=tag))
                    else:
                        warnings.append(_api_error(f"monitor_metrics[lqm {pid}]", lqm_resp))

            bandwidth: list[dict[str, Any]] = []
            if include_bandwidth:
                bw_payload = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "interval": interval,
                    "metrics": [
                        {"name": "BandwidthUsage", "statistics": ["average"], "unit": "Mbps"}
                    ],
                    "view": {"individual": "direction"},
                    "filter": {"site": [site_id]},
                }
                bw_resp = sdk.post.monitor_metrics(bw_payload)
                if getattr(bw_resp, "sdk_status", False):
                    bandwidth = _reduce(bw_resp)
                else:
                    warnings.append(_api_error("monitor_metrics[bandwidth]", bw_resp))

            result: dict[str, Any] = {
                "site_id": site_id,
                "site_name": site_names.get(site_id, site_id),
                "window_hours": hours,
                "total_paths": len(paths),
                "paths": paths,
                "link_quality": link_quality,
                "bandwidth": bandwidth,
            }
            if warnings:
                result["warnings"] = warnings
            return _fmt(result)
        except Exception as exc:
            return f"Error: {exc}"
