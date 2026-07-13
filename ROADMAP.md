# Roadmap

New Strata Cloud Manager / Prisma SASE API families land on
[pan.dev](https://pan.dev/sase/) faster than the SDK tracks them. This server
watches upstream automatically — the bundled endpoint catalog
(`resources/endpoint_catalog.json`) plus the **OpenAPI Spec Drift** section of
`scm_check_updates` flag new/changed spec files — and this file tracks what we
do about it.

## Recently shipped

- **PAB evidence in CE/NCSC CAF compliance** (2026-07-13) — BPA-PAB-001
  (browser device posture baseline: screen lock + disk encryption + host
  firewall → CAF-B5.a + new CE-SC-1 Secure Configuration control) and
  BPA-PAB-002 (stale enrolments >90 days → CAF-B5.a), skipping cleanly on
  unprovisioned tenants. Completes "PAB posture in tenant reporting".
  Also fixed a latent bug found on the way: `extract_browser` pointed at
  `/seb/api/v1` (404, silently empty) instead of `/seb-api/v1` — every
  browser_* snapshot field and the AS-BUILT §5 browser section had been
  empty since the extractor existed; real data now flows (14 users / 8
  devices / 100 apps on the lab MSSP tenant).
- **PAB in the NOC dashboard** (2026-07-13) — `scm_tenant_dashboard`
  gained a PAB column (`14u/8d (62%✓)` = users/devices/share of devices
  passing all three posture checks) from single-page `/seb-api` pulls
  inside the existing parallel poll. First live run flagged a lab tenant
  at 14% posture compliance. More tenants turned out to be
  PAB-provisioned than the licence API implies (5 of 9 serving data).
- **PAB tenant depth** (2026-07-13) — `scm_pab_inventory` /
  `scm_pab_apps` / `scm_pab_user_requests` over the previously untooled
  `access/browser-mgmt` family (33 paths, `/seb-api/v1/*`). Users,
  device inventory with endpoint posture (screen lock / disk encryption /
  firewall), groups, app catalog, and the user-request queue.
  Live-validated on a lab tenant (14 users, 8 devices across 4
  OSes — posture roll-up shows real gaps: 5/8 disk encryption). Base URL
  `api.sase.paloaltonetworks.com/seb-api/v1`, common SASE bearer;
  provisioning detected from the API (no `seb` license entry exists even
  on serving tenants — empty `/users` + "tenant not found" on
  `/applications` = unprovisioned). Feeds the remaining "PAB posture in
  tenant reporting" item (dashboard columns + CE/CAF evidence).
- **Standalone SaaS posture tool** (2026-07-13) — `scm_saas_posture`
  surfaces the SSPM data that was previously buried in compliance
  snapshots: onboarded apps with severity-ranked misconfig findings,
  Identity-SSPM IdP/NHI posture, and catalog capability counts, with
  manual JSON export (`save_to`) / offline import (`load_from`) using a
  format-tagged snapshot. Live-validated on bt-showcase (SSPM licensed,
  178-app catalog, zero apps onboarded — the tool renders the onboarding
  guidance path) and bt-sase-test-lab (unlicensed → clear message). Also
  added to the CLI Posture menu.
- **Classic Prisma SD-WAN depth (round 2)** (2026-07-12) — three more
  read-only tools over the monitor API, live-validated on the 16-site lab:
  `sdwan_flows` (top talkers per site — sources/destinations/apps by bytes
  with appdef name resolution, path-type split, dropped-flow count; the
  flow monitor takes one site per request), `sdwan_app_health` (healthscore
  buckets for sites/circuits/anynet links via `healthscore_type` +
  `aggregation` — the payload schema the round-1 note flagged as unknown —
  plus top-N apps/sites by 17 selectable bases via `monitor/topn`, and
  per-app healthscore via `applicationsummary/query`), and
  `sdwan_cellular_status` (module config joined to live status on
  `cellular_module_id`: modem/SIM/signal/firmware per element). The CLI's
  SD-WAN sub-menu also gained a MONITORING section exposing all of round
  1 + 2 plus WAN IP summary and the site map, reusing the tool logic via
  `_call_mcp_tool` (which now primes the tenant-config cache first).
- **WAN IP enrichment layer 3 — record + cross-check** (2026-07-12) —
  enrichment lookups persist in a 30-day local JSON cache (repeat AS-BUILT
  runs cost zero third-party calls); every WAN IP record now resolves its
  circuit (`circuit_name`/`wan_network` via interface → site WAN interface →
  WAN network); advisory drift flags compare observed ISP vs the configured
  circuit label (token overlap) and IP geolocation vs the site's configured
  coordinates (>500 km) — a live lab run flagged 8/53 circuits whose
  generic labels hid a shared BT egress; `scm_asbuilt_report` gained
  `enrich_wan_ips` (ISP/ASN/geo/drift columns in §4.2.1 and §3.4.7); and
  `sdwan_site_map` renders an interactive Leaflet/OSM HTML map from site
  lat/long (sites without configured coordinates are listed as skipped —
  12/16 in the main lab, which is also why geo-drift rarely fires there).
- **Classic Prisma SD-WAN depth (round 1)** — 5 new read-only tools on the
  existing `prisma-sase` session, live-validated against a 16-site lab
  tenant (2026-07-12): `sdwan_events` (alarm/alert feed with event-code
  resolution and severity summary), `sdwan_audit_logs` (403s gracefully on
  view-only roles), `sdwan_software_status` (per-ION version + staged
  upgrade state; found two stuck `download_cancelled` upgrades in the lab on
  first run), `sdwan_policy_rules` (path/QoS/NAT/NGFW-security rule
  contents + stacks), `sdwan_link_health` (per-path LQM latency/jitter/MOS
  + site bandwidth; the monitor API takes one path per LQM request, and
  `LqmPacketLoss` rejects every unit — omitted). Also fixed a latent bug:
  element software version is `software_version` not `sw_version`, so
  `sdwan_list_elements`, `sdwan_topology`, and the AS-BUILT §4.1 device
  table always showed it empty.
- **pan.dev endpoint catalog** — 1,593 endpoints / 23 families indexed with
  per-file blob SHAs; REST fallbacks resolve to exact documented URLs; spec
  drift surfaces in `scm_check_updates`.
- **Spec-driven tool scaffolding** — `scripts/gen_tool_from_spec.py` emits
  read-only tool scaffolds (typed params, docstrings) from any catalog family.
- **SP Interconnect visibility** — `scm_spi_status` (7 views: summary,
  interconnects, physical connections, regions, region connections, settings,
  IP-pool usage) over the `sase/mt-interconnect` family (Feb 2026). SPI is the
  service-provider backbone attach for Prisma Access (native-IP on-ramp).
- **Prisma Access Browser for MSP reporting** — `scm_pab_msp_summary`
  (users / tenants / CIE roll-ups per region) and `scm_pab_msp_report`
  (per-TSG blocked malware / websites / extensions and category breakdowns)
  over the `sase/pab-msp` family (Feb 2026).
- **Live WAN IP visibility** — `sdwan_wan_ip_summary` (public/private WAN IP
  per SD-WAN element interface, DHCP-leased included) and
  `scm_ngfw_wan_ip_summary` (NGFW interface IPs from running-config XML),
  plus AS-BUILT WAN IP tables (§4.2.1 SD-WAN with IP-annotated topology,
  §3.4.7 NGFW) — shipped 0.9.0.
- **SD-WAN geo + WAN IP ISP enrichment (layers 1–2)** — site `location`
  (lat/long) and full address surfaced in `sdwan_list_sites` and per-record
  in `sdwan_wan_ip_summary`; opt-in `enrich=true` on both WAN IP tools does
  a whatsmyip-style reverse lookup of each public IP (ISP, org, ASN, rDNS,
  geolocation) via `utils/ipenrich.py` — provider-pluggable (ip-api.com
  batch by default, ipinfo.io + token via `ip_enrichment_provider` /
  `ipinfo_token` settings), 6 h in-process cache, additive-only (failures
  degrade to warnings). Opt-in because it sends tenant public IPs to a
  third-party service (2026-07-11).
- **Detected post-NAT public IP per ION** — `sdwan_wan_ip_summary` now also
  returns `detected_public_ips`: the source address the cloud controller
  sees each element's config/events connection arriving from (element
  status `config_and_events_from`). Solves the NAT-hidden-WAN-IP case —
  live-validated: a lab branch holding an RFC1918 address on the wire
  resolved to its real ISP egress IP/ASN — without any on-device access
  (2026-07-11).
- **Widened endpoint catalog** — `gen_endpoint_catalog.py` previously only
  walked `openapi-specs/{sase,scm,access}`, three of ~19 top-level product
  dirs in the same pan.dev monorepo. Added `sdwan`, `dlp`, `dns-security`,
  `cloudngfw`, `cdl`, `email-dlp` (2026-07-09) — the adjacent security
  products an MSSP managing SASE/SCM tenants also touches. Catalog grew from
  1,593 endpoints / 23 families to **3,871 endpoints / 30 families**.
  Deliberately still excluded: `openapi-specs/mssp` (Prisma *Cloud's* MSSP
  backend — CSPM/CWPP tenant management, a different platform), and
  `compute`/`cwpp`/`cspm`/`dspm`/`iot`/`prisma-airs*` (thousands of files,
  different product lines entirely).

## Next

_Last pan.dev check: 2026-07-09 — no new API family since the bundled catalog
(`generated_at: 2026-07-03`). pan.dev's own changelog
(`/sase/docs/release-notes/changelog/`) tops out at 2026-02-23 (Prisma Browser
for MSP), and the last real content commit to `products/sase/api` was
2026-03-06 (Config Orchestration RNHP docs) — both already shipped or listed
below. `pan-scm-sdk` is current (`pyproject.toml` pins `>=0.15.1`, matching
PyPI latest). The gap right now is entirely in catalog families we haven't
built tools against yet, not in upstream drift._

- **Branch NAT IP, PA side (IKE peer IP per circuit)** — the SD-WAN side is
  done (see Recently shipped: element status `config_and_events_from` gives
  the post-NAT egress of the circuit the controller connection rides, and
  servicelink interface status exposes the full IKE/IPsec overlay state).
  What it can't give is the branch's NAT IP *per circuit* — that's what
  Prisma Access sees as the IKE peer on each RN tunnel. The right endpoint
  is Insights `tunnels/tunnel_list` (already used by the compliance
  snapshot), but every current service account gets HTTP 403 on it — same
  RBAC class as the known `allocated_ips` 403 (view-only roles). Blocked on
  a service account with an Insights/monitor read role; validate live, then
  join PA-side peer IP to SD-WAN servicelinks by service_endpoint. No
  remote-exec alternative exists: ION `toolkitsessions` endpoints are audit
  records of interactive Device Toolkit sessions, not a run-a-command API,
  and the SD-WAN events API 500s on bare queries (needs schema work).
- **ADEM path enrichment (branch → DC hop counts)** — `access/adem` (13
  paths, zero tooling) includes `/adem/telemetry/v2/measure/route/hops` —
  per-hop network path telemetry from ADEM synthetic tests — plus
  application/agent metric+score and internet-measure endpoints. Natural
  third dimension on top of the WAN IP work: WAN IP summary says *what
  circuit and ISP*, enrichment says *where and who*, ADEM route hops say
  *how the path actually performs* (hop count, per-hop latency
  branch → DC/app). Requires an ADEM-licensed tenant with agents/tests
  enabled for live validation — same rule as SPI/5G: don't scaffold blind.
- **Classic Prisma SD-WAN depth (round 3)** — rounds 1–2 (2026-07-12, see
  Recently shipped) covered events, audit logs, software, policy rules,
  link quality, flows/top talkers, app healthscore/top-N, and cellular
  module status. Still unbuilt from the 2,162-path
  `sdwan/legacy`+`sdwan/unified` families: application QoS aggregates
  (`monitor/aggregates/application/qos` — needs `filter.application_name`
  + `AggregateMetric{name,statistic,unit}`; metric names undocumented,
  probe live), interface-level status sweeps, IPFIX/SNMP config, and
  event-correlation policy config. Audit log + software history remain
  403 for current view-only service accounts — same blocker as Insights
  `tunnel_list`; revisit when a broader read role lands.
- **Configuration Orchestration (site-based Remote Networks)** — `sase/config-orch`,
  11 paths, **zero tooling**. Site + license workflow onboarding (the
  partner-facing RNHP site model) complementing the existing per-RN tooling.
- **5G Manage/Monitor** — `sase/manage-services-5g` (27 paths) +
  `sase/monitor-services-5g` (20 paths), **zero tooling**. Refreshed Oct 2025 /
  Feb 2026. Pick up when a 5G-enrolled tenant is available for live
  validation (same pattern as SPI — don't scaffold blind against a spec with
  no lab account to test 401/403 handling against).
- **Multitenant Notifications** — `sase/mt-notifications`, 10 paths, **zero
  tooling**. A tenant-level alert/notification feed is a natural NOC-dashboard
  fit (proactive alerting rather than pull-based polling) and nothing else in
  this roadmap depends on it, so it can be picked up independently.
- **Aggregate monitoring expansion** — `sase/mt-monitor`, 36 paths; only the
  alerts sub-resource is wired (`extract_mt_monitor_alerts`, used in
  compliance snapshots). Application usage, bandwidth consumption, and user
  analytics across tenants are unused — prime candidates for NOC dashboard
  depth.
- **Insights 2.0 resource catalog** — `access/insights`, 103 paths across 7
  spec files; only ~5 queries are hardcoded today (connected users v2/v3,
  per-SPN throughput in `scm_spn_bandwidth`). Custom queries, scheduled
  exports, and report downloads are unused.
- **SPI in documents and dashboards** — AS-BUILT §3 SP Interconnect section
  (interconnects, VLAN attachments, IP pools) and an SPI health column in the
  NOC dashboard. Blocked on access to an SPI-enrolled MSP-mode service
  account for live validation (current accounts get 401 on `/mt/sp-interconnect/*`).
- **Spec-schema request validation** — validate raw-REST query/body params
  against the OpenAPI schemas before calling (fewer opaque 400s).
- **Newly catalogued small families — scope before building** — `dlp`
  (standalone Enterprise DLP, 29 paths, includes a Beta Incidents API),
  `dns-security` (standalone Advanced DNS Security, 2 paths), `cloudngfw/aws`
  (Cloud NGFW-for-AWS marketplace API, 76 paths), `cdl/logforwarding` (6
  paths), `email-dlp` (3 paths). These are different products/subscriptions
  than SCM/SASE config — confirm a managed tenant actually holds the
  entitlement before scaffolding tools, rather than building against specs
  no lab account can exercise.

## How additions happen

1. `scm_check_updates` (or the spec-drift section) flags a new family/file.
2. Regenerate the catalog: `uv run --with pyyaml python scripts/gen_endpoint_catalog.py`.
3. Scaffold: `uv run --with pyyaml python scripts/gen_tool_from_spec.py <family>`.
4. Curate: consolidate endpoints into few ergonomic tools (tool count is
   client-visible context), add graceful 401/403/404/5xx rendering, live-test
   against a lab tenant, then register in `server.py` and `tools/reload.py`.
