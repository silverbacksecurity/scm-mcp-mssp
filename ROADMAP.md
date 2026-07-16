# Roadmap

New Strata Cloud Manager / Prisma SASE API families land on
[pan.dev](https://pan.dev/sase/) faster than the SDK tracks them. This server
watches upstream automatically — the bundled endpoint catalog
(`resources/endpoint_catalog.json`) plus the **OpenAPI Spec Drift** section of
`scm_check_updates` flag new/changed spec files — and this file tracks what we
do about it.

## Recently shipped

- **Agentic ops layer: verify / sentinel / gate** (2026-07-15) — three tool
  groups built on one section-diff engine (`audit/asbuilt_verify.py`):
  `scm_asbuilt_verify` (doc-vs-live drift check for AS-BUILT documents
  before customer handover), the drift sentinel (`scm_drift_baseline` /
  `scm_drift_check` / `scm_drift_result` — disk-persisted known-good
  baselines, HIGH/MEDIUM/LOW-triaged overnight sweep with background
  all-tenants jobs), and `scm_commit_preview` (pre-commit blast-radius
  gate: pending-change diff vs baseline, rule-shadow detection on the
  touched rules, BPA introduced/resolved delta, HIGH RISK/REVIEW/LOW RISK
  verdict). Candidate-vs-pushed note: the config-versions API can list and
  *load* versions but not read their content, so the gate diffs candidate
  extraction against the drift baseline — roll it forward with
  `update_baseline=true` after each approved push. Plus `scm_renewal_brief`
  (licences + bandwidth + live connected-MU count → renewal-conversation
  brief with over/under-consumption signals). All live-validated on a lab
  tenant. Completed the set with `scm_incident_rca` (2026-07-15): incident →
  root-cause correlation ranking config pushes, cert expiries, and licence
  expiries by temporal proximity (drift shown separately as state evidence),
  ending in a customer-facing RFO draft with cited evidence and an explicit
  correlation-not-causation caveat. SD-WAN status and Insights alerts are
  disclosed as unchecked (RBAC) rather than silently skipped — add them as
  evidence sources when a monitor-role service account lands.

- **Cross-tenant analytics (mt-monitor)** (2026-07-13) — `scm_mt_analytics`
  over the aggregation API: apps/threats/connectivity/incidents rolled up
  across the tenant hierarchy (`agg_by=tenant`), with CDL-region discovery
  (insights_region mapped + eu/uk sibling fallback; the lab tenants store in `uk`).
  Query language: `{"filter":{"rules":[...]},"properties":[...]}` from the
  spec examples — but `applications/list` 400s and `locationsUsers` 500s
  on the spec's own examples; revisit on a spec refresh. mt-notifications
  gateway path found (`/mt/notifications/api/cloud/2.0/...`) but 403 for
  current service accounts — joins the RBAC-blocked list.

- **PAN service-status / maintenance awareness** (2026-07-13) —
  `scm_service_maintenance` over the public status.paloaltonetworks.com
  Statuspage API (no auth/licence/RBAC; works when tenant APIs are down).
  SASE-product filtering (26 raw windows → 6 relevant on first run),
  region matching against `TenantConfig.insights_region` (global windows
  always included), per-tenant grouping, plus the page's overall
  indicator and unresolved SASE incidents. Same day: `status_banner()`
  now renders on `scm_tenant_dashboard` when status degrades, SASE
  incidents are open, or maintenance is due within 7 days — fetched
  concurrently, silent on failure, absent when healthy.
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
  format-tagged snapshot. Live-validated on a lab tenant (SSPM licensed,
  178-app catalog, zero apps onboarded — the tool renders the onboarding
  guidance path) and a second lab tenant (unlicensed → clear message). Also
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
  generic labels hid a shared carrier egress; `scm_asbuilt_report` gained
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

_Last pan.dev check: 2026-07-14 — one new spec file since the 2026-07-09
catalog: **Compliance Center v1** (`scm/config/posture-management/
compliance-framework/compliance-center-recent-v1.yaml`, 12 paths — see the
bullet below). Catalog regenerated (`generated_at: 2026-07-14`, 3,883
endpoints). No other upstream drift; the last content commit to
`products/sase/api` remains 2026-03-06 (Config Orchestration RNHP docs).
`pan-scm-sdk` is current (0.15.1 installed = PyPI latest); `prisma-sase`
and `mcp` also current._

- **SSR — Simple Service Requests (restricted customer-change CRUD)** — a
  single two-phase tool (working name `scm_ssr_execute`) automating the three
  commonest customer change requests: URL allow/block-listing, threat
  exceptions (include/exclude a threat ID in anti-spyware / vulnerability
  protection profiles), and SSL decryption include/exclude. All three reduce
  to one primitive — add/remove an entry in a designated SSR-managed object —
  so the "restricted to basic" property is structural, not policy: the tool
  only edits objects named in a per-tenant allowlist in settings.toml (e.g.
  `SSR-Allow-List` / `SSR-Block-List` / `SSR-Decrypt-Exclude` custom URL
  categories referenced once by existing rules at onboarding; profile
  `threat_exception` lists) and never touches a rulebase. Contract is
  machine-first, unlike every existing tool: JSON in/out for playbook
  branching, idempotent (re-adding an existing entry returns success +
  `already_present`, safe under orchestrator retries), `dry_run=True` default
  returning a before/after diff, mandatory `ticket_ref` echoed into the
  object description and commit message so the config carries its own
  provenance. Commit stays a separate explicit `scm_commit` step so the
  orchestrator owns sign-off. Intake is external and swappable — ServiceNow
  form or templated email → XSOAR playbook, or Teams form → Power
  Automate / Copilot Studio (MCP-native since 2025) — all mapping to the same
  dry-run diff → human approval → apply + commit flow. Validation stays
  server-side regardless of front-end (strict URL syntax, no over-broad
  wildcards, threat ID must exist; a compromised playbook still can't reach
  past the allowlisted objects). Prerequisites: auth on the SSE transport
  (bearer/mTLS — today the SSE port exposes every tool unauthenticated) and
  ideally a restricted entrypoint registering only the SSR surface + commit
  instead of the full tool set. SDK is ready now: `url_categories`,
  `decryption_rule`, `anti_spyware_profile`, and
  `vulnerability_protection_profile` all have full CRUD in pan-scm-sdk.
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
  tooling**. Gateway path confirmed live 2026-07-13
  (`/mt/notifications/api/cloud/2.0/agg/notifications/*`) but current
  service accounts get 403 Access denied — blocked on an MSP notifications
  role, same class as Insights `tunnel_list`.
- **Aggregate monitoring round 2** — `scm_mt_analytics` (2026-07-13, see
  Recently shipped) covers apps/threats/connectivity/incidents. Still
  unused: applicationUsage, urlLogs, upgrades/list, location trends, the
  custom license quota/utilization GETs, and the two endpoints that fail
  on their own spec examples (`applications/list`, `locationsUsers`).
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
- **Compliance Center API (new upstream 2026-07-14)** — `posture/
  compliance-frameworks/v1`, 12 paths, **zero tooling**. Framework
  definitions CRUD + clone + benchmark/un-benchmark, plus analytics:
  per-framework compliance scores, score timeline, configurations
  assessed, compliance controls, framework summaries, and benchmark
  monitoring with report download. Directly adjacent to the existing
  NCSC/NIST/ISO 27001/DSPT assessment tools — could replace or
  cross-check the local scoring in `scm_ncsc_assess`-family tools with
  PAN's own framework scoring, and "custom framework (CCF) + benchmark"
  maps naturally onto the MSSP per-customer baseline idea. Usual rule:
  probe live against a lab tenant first (new product surface — expect
  401/403 until the right role/entitlement exists), then curate into
  1–2 ergonomic tools rather than 12 endpoint wrappers.
- **Newly catalogued small families — scope before building** — `dlp`
  (standalone Enterprise DLP, 29 paths, includes a Beta Incidents API),
  `dns-security` (standalone Advanced DNS Security, 2 paths), `cloudngfw/aws`
  (Cloud NGFW-for-AWS marketplace API, 76 paths), `cdl/logforwarding` (6
  paths), `email-dlp` (3 paths). These are different products/subscriptions
  than SCM/SASE config — confirm a managed tenant actually holds the
  entitlement before scaffolding tools, rather than building against specs
  no lab account can exercise.

## Epic: Planner Agent — Agentic Orchestration Layer for scm-mcp-mssp

**Goal** — build a Planner Agent layer above the existing 125-tool
scm-mcp-mssp MCP server, following the PANW "NetSec Agents on SCM" taxonomy
(Persona → Planner → Expert Agents → Actions → Triggers), extended with an
MSSP cross-tenant orchestration layer that PANW's native single-tenant model
does not cover. The Planner decomposes high-level operator intent into
dynamic, persisted, auditable plans executed against the existing MCP tools.

**Architecture principle** — build the Planner loop once; expose three
trigger surfaces (scheduled/cron, conversational NLQ, IR/webhook) as entry
points into the same loop. Do not build three separate agents.

**Differentiation (do not cut)** — cross-tenant fan-out, tier-aware planning
(Gold/Silver/Bronze check depth), and customer-specific reporting are the
defensible layer versus PANW's roadmap. Single-tenant planning polish is
secondary.

Spec/design docs live in `docs/planner-agent/` (ARCHITECTURE.md,
TOOL_MANIFEST.md).

### Phase 1 — Tool taxonomy & safety rails ✅ shipped 2026-07-15

Delivered as `src/scm_mcp_mssp/resources/tools_manifest.yaml` (135 tools) +
the `scm_mcp_mssp.planner` loader with the non-overridable write-approval
rule, and a CI coverage test that fails whenever a tool is registered
without a manifest entry. See docs/planner-agent/TOOL_MANIFEST.md for the
implemented schema, API, and domain groupings. The "enforce in the
execution layer" item is delivered at the API layer (`requires_approval()`
has no bypass; unknown tools raise) — the loop that calls it is Phase 2.

- [x] Create a tool manifest (`tools_manifest.yaml` or similar) covering all
  125 MCP tools with fields:
  - `access: read | write` — write tools: `scm_commit`,
    `scm_security_rule_create`, `scm_security_rule_delete`,
    `scm_address_create`, `scm_address_delete`, `dlp_restore`,
    `scm_config_rollback`, `scm_config_push_track`, `scm_config_clone`,
    `mssp_onboard_tenant`, `mssp_evict_tenant`, `scm_cert_import`,
    `scm_tls_profile_manager` (create mode), `scm_apply_ncsc_baseline`,
    `scm_attach_ncsc_profiles`, `scm_create_ncsc_snippet`,
    `scm_create_nist_snippet`, `scm_reload`, `scm_restart`. Everything else
    defaults to read.
  - `domain`: one of deployment | threat_coverage | operational_health |
    posture_compliance | config_change | licensing | sdwan | certificates |
    identity | pab | dlp (mirrors PANW Expert Agent domains plus
    MSSP-specific ones)
  - `scope: tenant | cross_tenant` — cross_tenant: `mssp_tenant_dashboard`,
    `mssp_list_tenants`, `scm_cert_lifecycle`, `scm_mt_analytics`,
    `scm_incident_summary`, `mssp_tier_comparison`, `scm_discover_tenants`,
    `scm_licence_forecast`, `scm_service_maintenance`, `scm_spn_bandwidth`
    (all_tenants mode)
  - `idempotent: true | false` and `retry_policy: retry | fallback |
    fail_fast`
  - `known_failure_modes`: free text (e.g. `scm_remote_network_list` —
    Pydantic validation error on names with spaces and
    `bgp_peer.same_as_primary` field; fallback = `scm_ike_gateway_list`
    correlation)
- [x] Enforce a hard rule in the execution layer: `access: write` tools
  ALWAYS require explicit human approval before execution, regardless of
  trigger type. No config flag can disable this in v1.
- [x] Document per-domain tool groupings so the Planner loads only one
  domain's tools (~15–20) into context per sub-plan, keeping total loaded
  tools under the 128-tool Copilot Studio ceiling.

### Phase 2 — Planner loop core ✅ core shipped 2026-07-15

Delivered as the `scm_mcp_mssp.planner` package: schema/store/executor/
engine/loop (see docs/planner-agent/ARCHITECTURE.md status note). Claude
Opus 4.8 with structured outputs is the reasoning engine; the in-process
FastMCP backend is the first ToolBackend (Streamable-HTTP later). The
sub-plan delegation item is partial: `build_catalog(domains=[...])`
scopes context per domain, but a dedicated domain-executor wiring lands
with the Phase 3a MVP. Live-engine smoke pending an anthropic_api_key
in .secrets.toml (same credential as scm_ai_compliance_advisor).

- [x] Implement the loop: Trigger → Intent parse → Plan generation →
  Execute step → Observe result → Revise plan → repeat → Synthesis →
  Report/notify.
- [x] Define a persisted Plan schema (JSON, stored per run): `plan_id`,
  `trigger_type`, `trigger_payload`, persona/service-account identity,
  `tenant_scope` (single ID, list, or "all"), `goal`, ordered `steps[]` each
  with `{step_id, domain, tool, params, status:
  pending|running|ok|failed|skipped, result_summary, retries, started_at,
  finished_at}`, `revision_history[]`, `final_report_ref`.
- [x] Use Claude via the Anthropic API (tool-use) as the reasoning engine;
  the existing scm-mcp-mssp MCP server is the tool backend over Streamable
  transport (reuse the Copilot Studio transport work).
- [ ] Implement sub-plan delegation: Planner selects domain → domain-scoped
  executor runs with only that domain's tools loaded.
- [x] Failure policy in the loop: max 2 retries per step; on
  validation/schema errors use the manifest's fallback tool; on server
  timeout mark step failed and continue where the plan allows; always finish
  with a partial report rather than aborting the run. Plans must be
  resumable after MCP server restart (the server has known timeout/crash
  behaviour — treat this as a first-class scenario, and allow the Planner to
  invoke `scm_reload`/`scm_restart` as a recovery action with approval).
- [x] Full audit trail: every tool call, param set, and result summary
  persisted against the `plan_id`.

### Phase 3 — Trigger surfaces (priority order)

- [x] **3a. Scheduled ops agent (MVP — build first).** ✅ shipped 2026-07-15
  (`scm-planner-nightly`; acceptance findings fired on live estate data —
  see CHANGELOG). Email delivery still TODO (Slack webhook + file done).
  Original spec: Cron-triggered
  nightly run per tenant: tier assessment (`mssp_tier_assess`), cert scan
  (`scm_cert_scan`), licence expiry (`scm_license_info` /
  `scm_licence_forecast`), incident summary (`scm_incident_search`),
  job/change audit (`scm_list_jobs`). Output: ranked Markdown digest per
  tenant plus an estate-level summary, delivered via email/Slack. Findings
  ranked by severity then customer tier (Gold first). Acceptance test: the
  agent must autonomously surface a finding of the class "NFR licences
  expiring within 90 days across multiple tenants" and "licensed-but-unused
  tenant shell".
- [ ] **3b. Conversational copilot.** Slack/Teams frontend posting NLQ
  triggers into the same Planner loop; responses stream plan progress and
  final synthesis.
- [ ] **3c. IR-triggered agent (last).** Webhook from MT Monitor alerts /
  `scm_incident_search` into the Planner with pre-built triage plan
  templates (e.g. tunnel-down → `sdwan_wan_ip_summary`,
  `scm_ike_gateway_list`, `scm_list_jobs` recent changes, `sdwan_events`).
  Read-only triage in v1; remediation suggestions require approval.

### Phase 4 — MSSP cross-tenant layer

- [ ] Estate fan-out: a single trigger (e.g. "morning estate check")
  generates per-tenant sub-plans across all loaded tenants
  (`mssp_list_tenants`), executes with bounded concurrency, aggregates
  results.
- [ ] Tier-aware planning: read contracted tier per tenant
  (`mssp_tenant_dashboard`) and scope check depth accordingly — Bronze:
  licensing + cert + connectivity basics; Silver: + posture/compliance +
  change audit; Gold: full BPA/NCSC/ISO27001 assessments + DLP/SSPM posture.
- [ ] Cross-tenant anomaly rules: flag inconsistencies invisible to
  per-tenant analysis (e.g. tenant with SD-WAN topology but zero licences;
  duplicate NFR licence sets expiring across tenants; tenants with zero
  config jobs but full licence bundles).

### Constraints & risks

- Read-only operation for the first month of production use, even where
  approval gates exist. Write actions (`scm_commit` etc.) enabled only after
  the audit trail has been reviewed.
- PANW is building a native single-tenant Planner into SCM (NetSec Agents
  on SCM roadmap). Re-validate scope against PANW's timeline before
  investing beyond Phase 2 polish; keep investment weighted toward Phase 4
  (MSSP layer) and customer-specific reporting.
- MCP server stability is a known risk (timeouts, crashes, full disconnects
  observed); plan persistence + resumability is a hard requirement, not a
  nice-to-have.

### Estimate

- Credible scheduled-ops MVP (Phases 1, 2, 3a): ~4–6 weeks part-time given
  the Expert/tool layer already exists.

## How additions happen

1. `scm_check_updates` (or the spec-drift section) flags a new family/file.
2. Regenerate the catalog: `uv run --with pyyaml python scripts/gen_endpoint_catalog.py`.
3. Scaffold: `uv run --with pyyaml python scripts/gen_tool_from_spec.py <family>`.
4. Curate: consolidate endpoints into few ergonomic tools (tool count is
   client-visible context), add graceful 401/403/404/5xx rendering, live-test
   against a lab tenant, then register in `server.py` and `tools/reload.py`.
