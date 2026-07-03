# Roadmap

New Strata Cloud Manager / Prisma SASE API families land on
[pan.dev](https://pan.dev/sase/) faster than the SDK tracks them. This server
watches upstream automatically — the bundled endpoint catalog
(`resources/endpoint_catalog.json`) plus the **OpenAPI Spec Drift** section of
`scm_check_updates` flag new/changed spec files — and this file tracks what we
do about it.

## Recently shipped

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

## Next

- **SPI in documents and dashboards** — AS-BUILT §3 SP Interconnect section
  (interconnects, VLAN attachments, IP pools) and an SPI health column in the
  NOC dashboard. Blocked on access to an SPI-enrolled MSP-mode service
  account for live validation (current accounts get 401 on `/mt/sp-interconnect/*`).
- **PAB posture in tenant reporting** — PAB summary columns in
  `scm_tenant_dashboard`; PAB block-report evidence wired into Cyber
  Essentials / NCSC CAF browser-security controls.
- **Configuration Orchestration (site-based Remote Networks)** — site +
  license workflow onboarding tools from the `sase/config-orch` family
  (Mar 2026); complements the existing per-RN tooling with the partner-facing
  site model (RNHP).
- **Aggregate monitoring expansion** — the `sase/mt-monitor` family is ~95%
  untapped (application usage, bandwidth consumption, user analytics across
  tenants); prime candidates for NOC dashboard depth.
- **Insights 2.0 resource catalog** — custom queries, scheduled exports, and
  report downloads (`access/insights`, ~100 endpoints unused).
- **5G Manage/Monitor** — refreshed Feb 2026; pick up when 5G branches appear
  in managed estates.
- **Spec-schema request validation** — validate raw-REST query/body params
  against the OpenAPI schemas before calling (fewer opaque 400s).

## How additions happen

1. `scm_check_updates` (or the spec-drift section) flags a new family/file.
2. Regenerate the catalog: `uv run --with pyyaml python scripts/gen_endpoint_catalog.py`.
3. Scaffold: `uv run --with pyyaml python scripts/gen_tool_from_spec.py <family>`.
4. Curate: consolidate endpoints into few ergonomic tools (tool count is
   client-visible context), add graceful 401/403/404/5xx rendering, live-test
   against a lab tenant, then register in `server.py` and `tools/reload.py`.
