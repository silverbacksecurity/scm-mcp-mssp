# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **`scm_spi_status`** — Service Provider Interconnect visibility (pan.dev `sase/mt-interconnect`, Feb 2026): one view-based tool covering interconnect summary/inventory, physical connections, SPI regions, tenant settings, and IP-pool usage monitoring; actionable 401/403/404/5xx messages for accounts without an MSP role (`tools/mt_interconnect.py`)
- **`scm_pab_msp_summary` / `scm_pab_msp_report`** — Prisma Access Browser for MSP reporting (pan.dev `sase/pab-msp`, Feb 2026): region-level user/tenant/CIE roll-ups and per-TSG security-event reports (blocked malware, websites, extensions, category breakdowns) — browser-control evidence for CE/NCSC reporting (`tools/pab_msp.py`)
- **`scripts/gen_tool_from_spec.py`** — spec-driven tool scaffolding: emits read-only MCP tool scaffolds (typed query params, docstrings, graceful 4xx/5xx rendering) for any endpoint-catalog family, fetching specs pinned to the catalog's pan.dev commit; scaffolds are curated into consolidated tools before registration
- **`ROADMAP.md`** — tracks new pan.dev API families and planned coverage (SPI in AS-BUILT/NOC, PAB posture columns, Config Orchestration site-based RN, mt-monitor aggregates, Insights 2.0, 5G)
- **pan.dev endpoint catalog** — bundled index of 1,593 endpoints across 23 API families generated from the MIT-licensed pan.dev OpenAPI specs (`sase`, `scm`, `access` trees) with per-file git blob SHAs (`resources/endpoint_catalog.json` + loader `resources/endpoint_catalog.py`, regenerate via `scripts/gen_endpoint_catalog.py`); REST fallbacks in `audit.extractor` now resolve SDK resource names to their exact documented URL (override → SDK `ENDPOINT` → catalog → naive slug) instead of guessing a slug; `scm_check_updates` gains an **OpenAPI Spec Drift** section that diffs the bundled catalog's blob SHAs against the live pan.dev tree (4 unauthenticated GitHub API calls) and reports new/changed/removed spec files — new API families like SP Interconnect or Prisma Browser for MSP now surface automatically

## [0.6.0] - 2026-06-30

### Added
- **`scm_iso27001_assess`** — assessment of SCM/NGFW configuration against ISO/IEC 27001:2022 Annex A; maps all 39 BPA checks to 12 automatable controls (A.5.14 Information transfer, A.5.28 Collection of evidence, A.8.7 Malware protection, A.8.15 Logging, A.8.20 Network security, A.8.21 Network services/TLS, A.8.22 Network segregation, A.8.23 Web filtering, A.8.24 Cryptography, A.8.27 Secure architecture, A.8.28 Secure coding, A.8.29 Security testing); per-control compliance status with failing BPA checks and evidence guidance; overall verdict CONFORMING / MINOR NONCONFORMITY / MAJOR NONCONFORMITY; `clause_filter` parameter scopes to clause 5, 8, or specific control (e.g. 'A.8.22'); out-of-scope controls (governance, people, physical) explicitly noted; Markdown and JSON output (`tools/audit.py`, `audit/iso27001_controls.py`)
- **`scm_decrypt_policy_audit`** — deep-dive SSL/TLS decryption policy audit for a SCM folder; assesses profile quality (TLS min version ≥ 1.2, weak algorithm flags — 3DES, RC4, MD5, SHA-1, static RSA, forward-proxy block settings for expired/untrusted/unknown certs and unsupported versions), rule coverage (decrypt vs no-decrypt ratio, zone pairs, presence of any-any catch-all rule, disabled rules, rules missing a profile, inbound inspection), gap analysis with NCSC CAF D3.b and DSPT Standard 9 cross-references, and an overall verdict of ADEQUATE / PARTIAL / INSUFFICIENT; Markdown and JSON output (`tools/audit.py`)
- **`scm_dspt_assess`** — automated assessment of SCM/NGFW configuration against the NHS Data Security and Protection Toolkit (DSPT 2024-25 v5.1); covers technology Standards 7 (Continuity), 8 (Unsupported Systems), 9 (IT Protection), and 10 (Accountable Suppliers); maps all 39 BPA checks to 16 DSPT assertions; outputs per-assertion compliance status with DSPT-portal-ready evidence statements and overall level (Approaching / Meeting / Exceeding Standards); Markdown and JSON output with optional file save (`tools/audit.py`, `audit/dspt_controls.py`)
- **`scm_incident_search`** — search SCM security incidents via `POST /incidents/v1/search` with client-side filtering by severity (Critical/High/Medium/Low), status (Open/Closed/Acknowledged), product, and acknowledgement state; traffic-light emoji severity; multi-tenant `all_tenants=True` sweep (`tools/posture.py`)
- **`scm_incident_summary`** — cross-tenant NOC dashboard; counts Critical/High/Medium/Low/Total incidents per tenant with latest critical incident title; ideal for morning SLA briefings and MSSP weekly reports (`tools/posture.py`)
- **`scm_posture_report`** — retrieves Posture Management best-practice reports via `GET /posture/v1/reports`; graceful licence-gate handling (403 → actionable message) for tenants without the Posture Management add-on (`tools/posture.py`)
- **`scm_adnsr_list`** — list Advanced DNS Security Resolver resources (profiles, internal-domains, connection-sources, custom-fqdns, edl-definitions, misconfigured-domains, resolver-info, ca-certs) via `GET /adns-resolver/v1/{resource}`; licence-gate handling for tenants without the ADNSR subscription (`tools/adnsr.py`)
- **`scm_adnsr_profile_create`** — create an ADNSR DNS security profile with configurable default action (sinkhole/block/allow) and query logging via `POST /adns-resolver/v1/profiles` (`tools/adnsr.py`)
- **`scm_ngfw_local_config_list`** — list configuration versions pushed to a specific SCM-managed NGFW device via `GET /sse/config/v1/local-config/versions`; NGFW Operations entitlement required (`tools/adnsr.py`)
- **`scm_ngfw_local_config_get`** — fetch the XML configuration for a specific NGFW local config version (or `version="running"`) to enable automated BPA via `scm_aiops_bpa`; NGFW Operations entitlement required (`tools/adnsr.py`)
- **`scm_aiops_bpa`** — submit a PAN-OS device running config XML to the AIOps BPA API (`api.stratacloud.paloaltonetworks.com/aiops/bpa/v1`); implements the full 5-step workflow (POST `/requests` with device metadata → signed S3 upload URL → PUT XML → poll `/jobs/{id}` → GET `/reports/{id}` download URL → fetch and parse report); requires `requester_email` (a PANW CSP email registered in the AIOps BPA portal), `device_serial`, `device_family`, `device_model`, `device_version` as optional device metadata; renders findings as Markdown with overall score, per-category scores, and failing checks grouped by severity with recommendations; complements the 39 SCM SDK-based BPA checks with PAN's own device-level assessment engine (`tools/aiops.py`)
- **`scm_cert_lifecycle`** — multi-tenant TLS certificate lifecycle dashboard with `all_tenants=True` sweep across all MSSP tenants; identifies probable SSL inspection CA certs (name/CN heuristic) and flags them CRITICAL separately because expiry silently disables SSL decryption; produces cross-tenant summary table (total / flagged / SSL-CA critical / worst expiry) for NOC morning brief (`tools/ops.py`)
- **`scm_cert_import`** — import a PEM certificate into any SCM tenant folder via `POST /config/v1/certificates`; marks CA vs leaf type; prompts to commit after import (`tools/ops.py`)
- **`scm_tls_profile_manager`** — list (`action='list'`) or create (`action='create'`) TLS service profiles via `GET/POST /config/v1/tls-service-profiles`; created profiles default to TLS 1.2 minimum, AES-GCM only, no 3DES/RC4/SHA-1 — the NCSC-recommended cipher baseline (`tools/ops.py`)
- **BPA-SR-009** — NSF-ZT-1 zero trust rule specificity: flags allow rules where both `source=any` AND `destination=any`, giving zero network-level segmentation; distinct from BPA-SR-007 (which requires `app=any` too) and catches application-specific but location-unrestricted rules (`audit/bpa_checks.py`)
- **BPA-SR-010** — CE-FW-2 unauthenticated protocol exposure: flags allow rules that explicitly name unauthenticated or cleartext protocols (telnet, FTP, TFTP, rsh, rlogin, rexec, finger, SNMPv1/v2c, NetBIOS variants) with per-rule detail of which protocols are exposed and encrypted alternatives in remediation (`audit/bpa_checks.py`)
- NSF-ZT-1 and CE-FW-2 NCSC cross-references added to `BPA_TO_NCSC` for both new checks (`audit/ncsc_controls.py`)
- **`scm_config_versions`** — list all SCM config versions with commit timestamps, descriptions, admin, and human-readable age; marks the currently active running version; uses `GET /config/v1/config-versions` + `GET /config/v1/config-versions/running` (`tools/deployment.py`)
- **`scm_config_push_track`** — async config push with 10-second job polling, rich result table (duration, job ID, status %, warnings, device details), and optional `rollback_on_failure=True` that automatically loads the pre-push running version back to candidate if the job fails (`tools/deployment.py`)
- **`scm_config_rollback`** — load any saved config version back to candidate via `POST /config/v1/config-versions/{version}:load`; shows original commit metadata for confirmation; optional `commit_immediately=True` to push the rollback in one call (`tools/deployment.py`)
- **BPA-TP-007** — WildFire profile content coverage check: verifies profiles cover all high-risk file types (PE, PDF, MS-Office, JAR, ELF, APK, Flash) with direction=both and a block action on malicious verdicts; profiles with narrow file-type rules or missing block actions are flagged (`audit/bpa_checks.py`)
- **BPA-URL-002** — URL access profile block-category verification: checks that every URL access profile has explicit block rules for high-risk categories (malware, phishing, command-and-control, hacking, proxy-avoidance, dynamic-dns); profiles missing these blocks are listed as affected objects (`audit/bpa_checks.py`)
- **BPA-DEC-002** — Decryption rule coverage check: verifies that at least one decryption rule with `action=decrypt` is active in the rulebase; distinguishes between no profiles, no rules, and rules-but-only-exclusions failure modes (`audit/bpa_checks.py`)

### Changed
- **`scm_spn_bandwidth`** — now queries Prisma Access Insights v3.0 for live per-SPN throughput (Mbps in/out, 5-minute rolling average) and shows utilisation % against configured allocation; gracefully falls back to allocation-only mode if the tenant token lacks Insights scope (`tools/ops.py`, new `_insights_spn_throughput` helper)
- **`scm_tenant_dashboard`** — "Nearest Expiry" now excludes already-expired SKUs by default so the licence RAG reflects active renewal health rather than a long-dead legacy SKU (e.g. an old logging_service Production License) pinning every tenant to EXPIRED; new `include_expired=True` parameter restores the nearest-across-all-SKUs behaviour, and a tenant whose licences are all expired still flags red via a worst-SKU fallback (`tools/ops.py`, new `_nearest_licence_expiry` helper)
- **HTTP server** — bind address is now configurable via `SCM_MCP_HTTP_HOST` (defaults to `0.0.0.0` for containers) instead of being hardcoded (`server_http.py`)

### Tooling
- Re-enabled mypy type-checking on 7 of 8 previously-`ignore_errors` modules (only `audit/asbuilt_report` remains); fixed 3 latent type issues in `audit/insights_extractor` and `tools/mssp`
- Aligned the bandit SAST gate between CI and pre-commit (both fail on MEDIUM+); granted `pull-requests: read` to the PR-title and gitleaks CI jobs (previously 403-failing on every PR); resolved 5 MEDIUM bandit findings with real fixes / justified `nosec`
- Bumped all GitHub Actions to latest majors (`checkout` v7, `upload-artifact` v7, `setup-uv` v7, `build-push-action` v7, `setup-buildx-action` v4, `metadata-action` v6)
- Added 23 unit tests for the `tools/ops.py` pure helpers (cert/licence status thresholds, semver comparison, nearest-expiry selection)

### Added
- **`scm_cert_scan`** — scan all certificate objects across Shared, Remote Networks, Mobile Users, and Service Connections; flags CRITICAL (<30d), WARNING (<60d), CAUTION (<90d), EXPIRED; cross-references IKE gateways using cert auth vs PSK (`tools/ops.py`)
- **`scm_licence_forecast`** — licence expiry and seat utilisation per tenant; groups by app_id + expiry date, flags oversubscribed pools, `all_tenants=True` sweeps every MSSP tenant in one call (`tools/ops.py`)
- **`scm_tenant_dashboard`** — lightweight NOC wallboard; rules, remote networks, IKE tunnels, nearest licence expiry, and RAG status for every MSSP tenant in a single Markdown table; targeted REST calls only, no full snapshot extraction (`tools/ops.py`)
- **`scm_spn_bandwidth`** — SPN bandwidth allocation vs branch count; per-branch Mbps share, HIGH/MEDIUM/LOW oversubscription risk rating, QoS config, full branch roster per SPN, `all_tenants=True` mode (`tools/ops.py`)
- **`scm_gp_session_summary`** — live GP + Prisma Access Agent session count by country (GeoIP), compute node, client type, and GP version; compares connected sessions against licensed MU seat capacity and shows utilisation%; privacy-safe (aggregate counts only, no usernames or IPs) (`tools/ops.py`)
- **`scm_check_updates`** — checks PyPI for latest versions of `pan-scm-sdk`, `prisma-sase`, `mcp`, and `scm-mcp-mssp`; fetches `pan-scm-sdk` GitHub release notes and recent `pan.dev` SASE API commit log; shows 🟢/🟡/⚪ status per package (`tools/ops.py`)
- **`scm_restart`** — schedules a clean SIGTERM after returning the response so Claude Desktop or a supervisor can automatically reconnect; configurable `delay_seconds` (default 3, min 1) (`tools/reload.py`)
- **CLI: Check for Updates (`U`)** — new MANAGEMENT menu option; rich table of PyPI versions + pan-scm-sdk release notes + pan.dev SASE API recent commits (`cli.py`)
- **CLI: Restart MCP Server (`R`)** — new MANAGEMENT menu option; finds running `scm-mcp` / `scm-mcp-http` processes with `pgrep`, sends SIGTERM, offers to restart in background (`cli.py`)
- **Unique AS-BUILT Document ID** — every generated AS-BUILT now receives an `ASBUILT-YYYYMMDD-<8hex>` stamp shown in the document header and §1 Document Control table
- **Appendix E — SCM Configuration Change History** (§8.7) — last 20 SCM commits with date, user, type, result, and description automatically appended to every AS-BUILT

### Changed
- **HLD → AS-BUILT rebrand** — `hld_report.py` → `asbuilt_report.py`, `HLDReportBuilder` → `AsBuiltReportBuilder`, MCP tool `scm_hld_report` → `scm_asbuilt_report`, stamp prefix `HLD-` → `ASBUILT-`, output filenames `*-hld.*` → `*-asbuilt.*`; all docstrings, CLI labels, and docs updated
- **Reference architecture diagrams moved to Appendix F** (§8.8) — all four PAN Mermaid diagrams (Enterprise SASE, Prisma Access routing, SD-WAN dual-hub, MSSP hierarchy) removed from main body sections §2–§8; live AS-BUILT topology in §2.1 remains in the main body
- **Removed §8 MSSP Service & BAU Support Model** from AS-BUILT report — generic RACI/ITSM/escalation boilerplate replaced by live operational data tools; old §9 Appendices renumbered to §8

### Fixed
- **`oauth.token_expires_soon()` TypeError** — `token_expires_soon` is a `@property`, not a method; removed erroneous `()` call in `fetch_licenses`, `insights_extractor`, and `scm_mobile_user_stats` token-refresh paths

### Security
- **Purged customer report files from git history** — three previously committed report files removed from all commits using `git filter-repo`; force-pushed to GitHub
- **Hardened `.gitignore`** — `reports/`, `*.docx`, `*hld*.md`, `*asbuilt*.md`, `*bpa-*.md`, `*ncsc-*.md`, `bt-*.md`, `BT-*.md`, `tenant-*.md`, `backups/`, `ai-design-components/`; generated reports will never be accidentally committed

### Known Gaps


- `scm_aiops_bpa` integrated and working but requires **AIOps BPA portal registration**: the API (`/aiops/bpa/v1/requests`) validates `requesterEmail` against PAN's AIOps BPA user database independently of PANW CSP auth — service account emails (`.iam.panserviceaccount.com`) are rejected as the portal requires a registered human CSP user email; contact bpa@paloaltonetworks.com or register at aiops.paloaltonetworks.com to enable; once enabled the tool is fully functional
- No CRUD on: services, service groups, decryption rules, application override rules
- No identity/auth server profile CRUD (RADIUS, LDAP, SAML, TACACS+, Kerberos) — list only via extractor
- GlobalProtect Mobile Agent config resources (agent profiles, tunnel profiles) available in SDK v0.15.0 but no dedicated CRUD MCP tools yet
- `scm_posture_report`, `scm_adnsr_*`, and `scm_ngfw_local_config_*` are implemented but return 403 in non-subscribed tenants — Posture Management and Advanced DNS Security Resolver require separate PAN add-on subscriptions; NGFW Operations requires the NGFW Operations entitlement on the TSG

## [0.4.7] - 2026-06-22

### Added
- `scm_browser_list` — Prisma Browser (RBI) device/user/application group inventory via `/seb/api/v1/`
- `scm_airs_list` — Prisma AIRS (AI Runtime Security) customer apps, profiles, and deployment profiles
- `scm_ngfw_device_list` — NGFW managed devices with model, serial, HA state, and connection status
- GlobalProtect agent profile and tunnel profile sections in AS-BUILT report (§3 Mobile Users)
- NGFW health and HA status sections added to AS-BUILT report

### Fixed
- SD-WAN `sdwan_list_wan_interfaces` and `sdwan_debug_topology` API path corrections
- Mobile-agent REST fallback URLs corrected for GP agent/tunnel profile endpoints

## [0.4.6] - 2026-06-20

### Added
- `scm_ai_compliance_advisor` — AI-powered compliance advisor combining NCSC/NIST gap checks with Claude-generated executive summary and remediation playbook (`tools/ai_advisor.py`)
- `scm_nist_gap` — NIST CSF v2.0 / SP 800-53 Rev 5 gap analysis remapping NCSC structural checks to NIST control identifiers
- `scm_create_nist_snippet` — create reusable SCM snippet with NIST-compliant security profiles and NIST-Compliant tag

## [0.4.5] - 2026-06-19

### Added
- `scm_create_ncsc_snippet` — create a reusable SCM snippet containing NCSC-compliant security profiles (anti-spyware, vulnerability, WildFire, URL, log forwarding, tag); distinct from folder-scoped `scm_apply_ncsc_baseline`
- AS-BUILT report: Markdown-to-Word (docx) conversion via `python-docx`; `output_format='docx'` now works without pandoc

## [0.4.4] - 2026-06-19

### Added
- `scm_list_jobs` — list SCM commit/push jobs with username, type, result, and timestamps for commit audit history
- Tenant metadata cache: tenant label and region stored at auth time for use in AS-BUILT and tier reports

### Fixed
- `scm_asbuilt_report` §8 MSSP Service Model always rendered (was silently skipped on partial data)
- AS-BUILT VPN crypto tables always populated from IKE/IPSec objects

## [0.4.3] - 2026-06-18

### Added
- `scm_mobile_user_stats` — live Prisma Access connected user count and bandwidth allocation via Prisma Access Insights API
- `dlp_backup` and `dlp_restore` — export and restore both SCM inline DLP and Enterprise DLP configuration across tenants

### Fixed
- 5xx error suppression across all extractor paths — non-fatal API errors no longer abort full AS-BUILT/backup runs
- SSE REST fallback URLs corrected for mobile-agent resource endpoints

## [0.4.2] - 2026-06-18

### Added
- `scm_ztna_connector_list` — ZTNA Connector inventory via `/sse/connector/v2.0/api/`
- `scm_dlp_list` — SCM inline DLP data-filtering profiles and data objects
- `scm_casb_list` — CASB SaaS tenant restriction policies
- `dlp_enterprise_list` — Enterprise DLP data patterns and ML-based profiles from `api.dlp.paloaltonetworks.com`

## [0.4.1] - 2026-06-17

### Added
- `scm_license_info` — Prisma SASE subscription licence inventory with SKU, seat count, and expiry via `/subscription/v1/licenses`
- CLI management menu: tenant onboarding option (A) added

### Fixed
- `fetch_licenses` in `oauth.py` — corrected auth header construction for subscription API

## [0.3.0] - 2026-06-17

### Added

#### MSSP Tier System (`audit/tiers.py`)
- `TierDefinition` frozen dataclass — specifies required BPA check severities, NCSC framework scope, SCM snippet names, and commercial feature description per tier
- Three tier definitions:
  - **Bronze** — Cyber Essentials baseline: Critical-only BPA checks, CE v3.2 framework, 2 SCM snippets (`MSSP-Bronze-SecurityProfiles`, `MSSP-Bronze-Policies`)
  - **Silver** — Cyber Essentials Plus: Critical + High BPA checks, CE v3.2 + 10 Steps, 4 SCM snippets (adds WildFire, DNS security, log forwarding, zone protection)
  - **Gold** — NCSC CAF v4.0 full: All BPA checks (Critical + High + Medium + Low), all frameworks, 6 SCM snippets (adds SSL/TLS decryption profiles + policies)
- `score_findings_against_tier(findings, tier)` — separates findings into tier-required breaches vs out-of-scope advisory, returns compliance score percentage
- `upgrade_gap(findings, from_tier, to_tier)` — identifies blocking findings, new NCSC controls, and additional snippets needed to upgrade tier
- `SNIPPET_TEMPLATES` — content specifications for all 12 tier SCM snippets (Bronze ×2, Silver ×4, Gold ×6); used by onboarding tool to guide snippet creation
- `TIER_ORDER` list (`["bronze", "silver", "gold"]`) for ordered tier traversal
- Tier hierarchy is a strict superset chain: every Silver requirement is also a Gold requirement; every Bronze requirement is also a Silver requirement

#### MCP Tools — MSSP Tier Management (`tools/mssp.py`)
- `mssp_tier_assess` — score a folder against a contracted tier; returns JSON with `tier_compliant`, `compliance_score_pct`, `breaches`, `advisory`, and automatic upgrade gap count
- `mssp_tier_report` — customer-facing Markdown compliance report with visual compliance bar, breach remediation steps, advisory upsell context, and upgrade path section; optional `save_to` path
- `mssp_upgrade_path` — JSON gap analysis between any two tiers: blocking findings, additional NCSC controls, snippets to apply, new features
- `mssp_onboard_tenant` — checks which tier snippets exist in SCM, associates present ones with the customer folder; `dry_run=True` by default to preview before execution; `create_folder=True` creates the folder if needed
- `mssp_tenant_dashboard` — Markdown dashboard of all currently loaded MSSP tenants
- `mssp_snippet_catalogue` — Markdown catalogue of all tier snippet templates and content specifications, filterable by tier
- `mssp_tier_comparison` — side-by-side Gold / Silver / Bronze feature comparison table (suitable for sales / customer conversations)

#### TenantConfig additions (`config/settings.py`)
- `tier: ServiceTier` field (default `"bronze"`) — `Literal["gold", "silver", "bronze"]`; loaded from `settings.toml` `[tenants.*]` blocks
- `service_term_years: int` field (default `1`, range 1–3) — contract duration in years
- `account_ref: str` field — CRM / ticketing system reference for cross-system linking
- `ServiceTier` type alias exported from `config/settings.py`

#### Settings template (`settings.toml`)
- `[tenants.*]` block template extended with `tier`, `service_term_years`, and `account_ref` fields with inline documentation
- Tier descriptions added as comments explaining the three-tier NCSC framework mapping

#### Tests (`tests/unit/test_tiers.py`)
- 33 new unit tests across 5 test classes:
  - `TestTierDefinitions` — existence, hierarchy (superset chain), NCSC coverage, snippet non-empty
  - `TestTierScoring` — breach vs advisory separation at each tier, WARN counts as breach, compliance score maths
  - `TestUpgradeGap` — blocking detection, new snippet identification, NCSC control delta, two-tier skip
  - `TestTenantConfigTierField` — default values, accepted values, optional fields

## [0.2.0] - 2026-06-17

### Added

#### Audit Engine (`audit/` subpackage)
- `AuditSnapshot` dataclass — flat, SDK-agnostic representation of all auditable SCM config for a folder/tenant
- `AuditExtractor` (`audit/extractor.py`) — pulls 30+ resource types from SCM via the SDK into an `AuditSnapshot`; non-fatal per-resource error capture so partial data still produces findings
- `Finding` dataclass with `Severity` (critical/high/medium/low/info) and `Status` (fail/pass/warn/skip) enums
- `bpa_checks.py` — 21 PAN Best Practice Assessment checks across six categories:
  - **Security Rules** (SR-001–008): no-profile allow rules, permit-any-any, logging at session end, disabled rule hygiene, app-any allow rules, deny rule logging, unrestricted outbound, explicit deny-all
  - **Threat Prevention** (TP-001–006): anti-spyware with DNS sinkholing, DNS security profiles, vulnerability protection profiles, WildFire profiles, file blocking profiles, SSL/TLS decryption profiles
  - **URL Filtering** (URL-001): URL category configuration check
  - **Zone Protection** (ZP-001): zones without zone protection profiles
  - **Logging** (LOG-001–003): log forwarding profiles, syslog server profiles, allow rules missing log forwarding
  - **Network** (NET-001–002): minimum zone segmentation, remote network IPSec configuration
- `ncsc_controls.py` — 16 NCSC control definitions across four frameworks:
  - CAF v4.0 (August 2025): B2.a/b/c, B3.a/b, B4.a, C1.a/b
  - Cyber Essentials v3.2: CE-FW-1/2/3/4
  - 10 Steps to Cyber Security: 10S-NS-1/2/3, 10S-TP-1
  - Network Security Fundamentals: NSF-ZT-1, NSF-LOG-1
- `BPA_TO_NCSC` mapping — cross-references every BPA check ID to its applicable NCSC control IDs
- `ReportBuilder` (`audit/report.py`) — renders findings as structured JSON (SIEM-ingestible) or Markdown (AS-BUILT AS-IS document) with executive summary, config inventory table, severity-grouped findings with remediation, NCSC control index

#### MCP Tools — Audit (`tools/audit.py`)
- `scm_config_backup` — exports complete config snapshot to timestamped JSON file; records resource counts and non-fatal extraction errors; respects `SCM_MCP_BACKUP_DIR` env var
- `scm_bpa_assess` — runs all BPA checks against live SCM config; supports `severity_filter` and `failed_only` parameters; returns JSON findings with NCSC cross-references
- `scm_ncsc_assess` — control-by-control NCSC compliance view; filterable by framework (`caf`/`ce`/`10steps`/`all`); returns compliant/non-compliant/not-assessed per control with linked findings
- `scm_audit_report` — combined BPA + NCSC Markdown or JSON report (AS-BUILT); optional `save_to` path writes report to disk
- `scm_config_diff` — compares two backup JSON files; returns structured diff of added/removed/modified objects per resource type; suitable for pre/post change-window auditing

#### References
- pan.dev `aiops-ngfw-bpa` product directory identified as source for BPA API spec (`BPAReportAPI.yaml`)
- PAN AIOps BPA API endpoint documented: `api.stratacloud.paloaltonetworks.com/aiops/bpa/v1`
- NCSC CAF v4.0 (published August 2025), Cyber Essentials v3.2, NCSC 10 Steps, and Network Security Fundamentals used as compliance sources
- `panos-to-scm` (github.com/PaloAltoNetworks/panos-to-scm, archived Aug 2024) used as resource type completeness checklist

## [0.1.0] - 2026-06-17

### Added

#### Core Infrastructure
- `uv`-managed Python 3.12 project with `src/` layout and `hatchling` build backend
- `pyproject.toml` with `[project.scripts]` entry point (`scm-mcp`)
- `pydantic-settings` `Settings` class with `SCM_MCP_` env prefix for all server config
- Per-tenant `TenantConfig` (Pydantic model) with `SecretStr` client secret and field validation
- `dynaconf` integration for multi-tenant credential loading from `settings.toml` / `.secrets.toml`
- Thread-safe per-tenant `Scm` client cache in `auth/oauth.py` with `evict_tenant` for credential rotation
- Structured JSON logging via `structlog` with ISO timestamps and noisy-library suppression
- Custom exception hierarchy: `ScmMcpError`, `TenantNotFoundError`, `AuthenticationError`, `ResourceNotFoundError`, `ValidationError`

#### MCP Server (`server.py`)
- `FastMCP` server (`scm-mcp-mssp`) with `stdio` and `SSE` transport support (`--transport`, `--host`, `--port` flags)
- MSSP multi-tenant client resolver: routes `tenant_id` argument to correct cached `Scm` client in MSSP mode, falls back to default credentials in single-tenant mode
- Eager tenant pre-loading from `settings.toml` `[tenants.*]` blocks on startup when `SCM_MCP_MSSP_MODE=true`
- Startup authentication validation for default (single-tenant) credentials

#### MCP Tools — Objects (`tools/objects.py`)
- `scm_address_list` — list address objects with optional name filter
- `scm_address_get` — fetch single address object by name
- `scm_address_create` — create address object (ip_netmask / fqdn / ip_range)
- `scm_address_delete` — delete address object by name
- `scm_address_group_list` — list address groups
- `scm_service_list` — list service objects
- `scm_tag_list` — list tags
- `scm_edl_list` — list external dynamic lists

#### MCP Tools — Security (`tools/security.py`)
- `scm_security_rule_list` — list security rules with pre/post position support
- `scm_security_rule_get` — fetch single security rule by name
- `scm_security_rule_create` — create security rule (zones, addresses, applications, services, profile groups)
- `scm_security_rule_delete` — delete security rule by name
- `scm_anti_spyware_profile_list` — list anti-spyware profiles
- `scm_url_category_list` — list URL categories

#### MCP Tools — Network (`tools/network.py`)
- `scm_zone_list` — list security zones
- `scm_nat_rule_list` — list NAT rules with pre/post position support
- `scm_nat_rule_get` — fetch single NAT rule by name
- `scm_ike_gateway_list` — list IKE gateways
- `scm_ipsec_tunnel_list` — list IPSec tunnels
- `scm_dns_server_list` — list DNS server profiles

#### MCP Tools — Deployment (`tools/deployment.py`)
- `scm_remote_network_list` — list remote networks (branch / SD-WAN connections)
- `scm_remote_network_get` — fetch single remote network by name
- `scm_service_connection_list` — list service connections (cloud / DC interconnects)
- `scm_bandwidth_allocation_list` — list Prisma Access bandwidth allocations
- `scm_commit` — commit candidate config for one or more folders (synchronous, 300s timeout)
- `scm_job_status` — poll status of an async SCM job

#### MCP Tools — Setup & MSSP (`tools/setup.py`)
- `scm_folder_list` — list SCM folders (customer hierarchy)
- `scm_folder_get` — fetch single folder by name
- `scm_device_list` — list onboarded devices (firewalls, Panorama)
- `scm_snippet_list` — list configuration snippets
- `mssp_list_tenants` — list all currently loaded tenant IDs
- `mssp_evict_tenant` — remove cached client to force re-authentication after credential rotation

#### MCP Resources (`resources/tenant.py`)
- `scm://tenants` — index of all loaded tenants
- `scm://tenants/{tenant_id}` — per-tenant authentication status
- `scm://tenants/{tenant_id}/folders` — folder list for a given tenant

#### Configuration & Secrets
- `settings.toml` — dynaconf config with `[tenants.*]` multi-tenant block template
- `.secrets.toml.example` — per-tenant secret template (git-ignored at `.secrets.toml`)
- `.env.example` — all `SCM_MCP_*` environment variables documented

#### Developer Tooling
- `ruff` linting and formatting (line length 100, `E F I UP B SIM` rules)
- `mypy` strict type checking with `pydantic.mypy` plugin
- `pre-commit` hooks: ruff, ruff-format, trailing whitespace, YAML/TOML check, private key detection, no-commit-to-main
- GitHub Actions CI workflow: lint → format check → mypy → pytest on push/PR
- `pytest` with `pytest-asyncio` and `pytest-cov` configured
- Unit tests: `TestTenantConfig` (valid config, empty ID validation, secret not leaked in repr) and `TestSettings` (defaults, env override) and `TestClientCaching` (cache hit, eviction, unknown tenant error)

[Unreleased]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.7...HEAD
[0.4.7]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/silverbacksec/scm-mcp-mssp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/silverbacksec/scm-mcp-mssp/releases/tag/v0.1.0
