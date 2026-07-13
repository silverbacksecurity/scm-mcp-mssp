# SCM MCP MSSP — Tool Reference

> Auto-generated from source docstrings. Do not edit manually — run `uv run python scripts/gen_docs.py` to regenerate.

All tools authenticate via Bearer-token OAuth (SASE client credentials) configured in `settings.toml` / `.secrets.toml`.

**123 tools** across 19 modules.

## Table of Contents

- [Objects](#objects)
- [Security Policy & Profiles](#security-policy--profiles)
- [Network](#network)
- [Deployment & Connectivity](#deployment--connectivity)
- [Setup & Tenant Management](#setup--tenant-management)
- [Audit & Reporting](#audit--reporting)
- [NCSC Baseline](#ncsc-baseline)
- [Enterprise DLP](#enterprise-dlp)
- [MSSP Multi-Tenant](#mssp-multi-tenant)
- [Prisma SD-WAN](#prisma-sd-wan)
- [Operational Visibility](#operational-visibility)
- [Posture Management](#posture-management)
- [Advanced DNS Security & NGFW Operations](#advanced-dns-security--ngfw-operations)
- [AIOps](#aiops)
- [AI Compliance Advisor](#ai-compliance-advisor)
- [Service Provider Interconnect](#service-provider-interconnect)
- [Prisma Access Browser for MSP](#prisma-access-browser-for-msp)
- [Utility](#utility)
- [Pab](#pab)

---

## Objects

_Addresses, address groups, services, tags, EDLs._

### `scm_address_list`

List address objects in a SCM folder.

```
Args:
    folder: SCM folder (customer context for MSSP).
    tenant_id: SCM tenant ID; uses default tenant when omitted.
    limit: Maximum number of results.
    name_filter: Substring filter on address name.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |
| `name_filter` | `str` | `''` |

### `scm_address_get`

Fetch a single address object by name.

```
Args:
    name: Address object name.
    folder: SCM folder.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_address_create`

Create an address object in SCM.

```
Provide exactly one of ip_netmask, fqdn, or ip_range.

Args:
    name: Object name.
    folder: SCM folder.
    ip_netmask: CIDR notation (e.g. 10.0.0.0/8).
    fqdn: Fully qualified domain name.
    ip_range: IP range (e.g. 10.0.0.1-10.0.0.100).
    description: Optional description.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `ip_netmask` | `str` | `''` |
| `fqdn` | `str` | `''` |
| `ip_range` | `str` | `''` |
| `description` | `str` | `''` |
| `tenant_id` | `str` | `''` |

### `scm_address_delete`

Delete an address object by name.

```
Args:
    name: Address object name.
    folder: SCM folder.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_address_group_list`

List address groups in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum number of results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_service_list`

List service objects in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum number of results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_tag_list`

List tags in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum number of results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_edl_list`

List external dynamic lists (EDLs) in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum number of results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

---

## Security Policy & Profiles

_Security rules (CRUD), Anti-Spyware profiles, URL categories._

### `scm_security_rule_list`

List security policy rules in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum number of results.
    position: Rule position — 'pre' or 'post'.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |
| `position` | `str` | `'pre'` |

### `scm_security_rule_get`

Fetch a single security rule by name.

```
Args:
    name: Rule name.
    folder: SCM folder.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_security_rule_create`

Create a security policy rule.

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `action` | `str` | `—` |
| `source_zones` | `list[str]` | `—` |
| `destination_zones` | `list[str]` | `—` |
| `source_addresses` | `list[str] \| None` | `None` |
| `destination_addresses` | `list[str] \| None` | `None` |
| `applications` | `list[str] \| None` | `None` |
| `services` | `list[str] \| None` | `None` |
| `profile_setting` | `dict[str, Any] \| None` | `None` |
| `description` | `str` | `''` |
| `disabled` | `bool` | `False` |
| `tenant_id` | `str` | `''` |

### `scm_security_rule_delete`

Delete a security rule by name.

```
Args:
    name: Rule name.
    folder: SCM folder.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_anti_spyware_profile_list`

List anti-spyware profiles in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_url_category_list`

List URL filtering categories in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

---

## Network

_Zones, NAT rules, IKE gateways, IPSec tunnels, DNS servers._

### `scm_zone_list`

List security zones in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_nat_rule_list`

List NAT rules in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
    position: Rule position — 'pre' or 'post'.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |
| `position` | `str` | `'pre'` |

### `scm_nat_rule_get`

Fetch a single NAT rule by name.

```
Args:
    name: NAT rule name.
    folder: SCM folder.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_ike_gateway_list`

List IKE gateways in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_ipsec_tunnel_list`

List IPSec tunnels in a SCM folder.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_dns_server_list`

List internal DNS servers for the tenant.

```
Internal DNS servers are a deployment-global resource (not folder-scoped),
so the ``folder`` argument is accepted for interface consistency but not
used to filter results.

Args:
    folder: SCM folder (unused — kept for interface consistency).
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

---

## Deployment & Connectivity

_Remote Networks, Service Connections, Bandwidth Allocations, config versions, jobs._

### `scm_remote_network_list`

List remote networks (branch/SD-WAN connections) in SCM.

```
Args:
    folder: SCM folder (unused — remote networks always live in the
            fixed "Remote Networks" container; kept for interface
            consistency with the other _list tools).
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_remote_network_get`

Fetch details for a single remote network.

```
Args:
    name: Remote network name.
    folder: SCM folder (unused — see scm_remote_network_list).
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_service_connection_list`

List service connections (cloud/DC interconnects) in SCM.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_bandwidth_allocation_list`

List bandwidth allocations for Prisma Access compute locations.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_commit`

Commit pending SCM configuration changes.

```
Commits the candidate config for the listed folders.  This is
the equivalent of 'commit' on a firewall — required after any
create/update/delete operation to make changes effective.

Args:
    folders: Folders whose changes to commit.
    description: Commit description / change ticket reference.
    tenant_id: SCM tenant ID.
    admin: Optional admin name to attribute the commit to.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folders` | `list[str]` | `—` |
| `description` | `str` | `''` |
| `tenant_id` | `str` | `''` |
| `admin` | `str` | `''` |

### `scm_job_status`

Check the status of an asynchronous SCM job (e.g. commit).

```
Args:
    job_id: Job ID returned by commit or other async operations.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `job_id` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_list_jobs`

List SCM configuration jobs (commits, pushes) showing who triggered each one.

```
Returns recent jobs ordered newest-first, including the SCM username (uname)
who triggered each job, the job type, result, timestamps, and description.
Use this to audit commit history, find who last changed config, or investigate
failed pushes.

Job types include: Commit, CommitAndPush, NGFW_Push, PA_Push.
Result values: OK, FAIL, PENDING, RUNNING.

Args:
    tenant_id: SCM tenant ID. Defaults to the configured default tenant.
    limit: Maximum jobs to return (default 50, max 200).
    offset: Pagination offset.
    job_type: Optional filter — e.g. "Commit" or "NGFW_Push".
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `50` |
| `offset` | `int` | `0` |
| `job_type` | `str` | `''` |

### `scm_config_versions`

List SCM configuration versions with timestamps, descriptions, and running state.

```
Shows the full version history of committed configs for this tenant.
The running version is the currently active config on Prisma Access.
Use version numbers with scm_config_rollback to revert to a prior state.

Args:
    tenant_id: SCM tenant ID. Defaults to the configured default tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `scm_config_push_track`

Push candidate config with async job tracking and optional auto-rollback.

```
Unlike scm_commit (which blocks silently), this tool polls the job every
10 seconds and streams progress, then returns a rich result including
warnings, affected devices, push duration, and rollback status if used.

When rollback_on_failure=True, if the push job fails the tool automatically
loads the last known-good running version back to candidate — so the next
commit restores the previous state.

Args:
    folders: Folders whose changes to push (e.g. ["Prisma Access"]).
    description: Commit description or change-ticket reference.
    timeout: Max seconds to wait for the push job (default 300).
    rollback_on_failure: If True, auto-load the previous running version on failure.
    tenant_id: SCM tenant ID. Defaults to the configured default tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folders` | `list[str]` | `—` |
| `description` | `str` | `''` |
| `timeout` | `int` | `300` |
| `rollback_on_failure` | `bool` | `False` |
| `tenant_id` | `str` | `''` |

### `scm_config_rollback`

Load a previous SCM config version back to candidate for recommit.

```
This is a two-phase safety operation:
  1. Load — copies the specified version into the candidate config
  2. Commit — optional; if commit_immediately=True, commits the candidate right away

Run `scm_config_versions` first to see the version history.

Args:
    version: The config version number to roll back to.
    commit_immediately: If True, commit the loaded version immediately after loading.
    description: Commit description when commit_immediately=True.
    tenant_id: SCM tenant ID. Defaults to the configured default tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `version` | `int` | `—` |
| `commit_immediately` | `bool` | `False` |
| `description` | `str` | `''` |
| `tenant_id` | `str` | `''` |

---

## Setup & Tenant Management

_Folders, devices, snippets, tenant list/evict._

### `scm_folder_list`

List SCM folders (represents the tenant/customer hierarchy).

```
Args:
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_folder_get`

Fetch a single SCM folder by name.

```
Args:
    name: Folder name.
    tenant_id: SCM tenant ID.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_device_list`

List devices (firewalls, Panorama) onboarded to SCM.

```
Args:
    folder: SCM folder.
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `scm_snippet_list`

List configuration snippets available in SCM.

```
Args:
    tenant_id: SCM tenant ID.
    limit: Maximum results.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `limit` | `int` | `200` |

### `mssp_list_tenants`

List all MSSP tenant IDs that currently have active SCM clients.

```
Returns which tenants are loaded and ready without needing
re-authentication.
```

### `mssp_evict_tenant`

Remove a tenant's cached SCM client (forces re-authentication on next use).

```
Use this after rotating OAuth2 credentials for a customer tenant.

Args:
    tenant_id: SCM tenant ID to evict.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `—` |

---

## Audit & Reporting

_Configuration backup, BPA, NCSC/NIST/DSPT/ISO 27001, AS-BUILT & HLD reports, config diff & clone._

### `scm_config_backup`

Export a complete SCM configuration snapshot to a JSON backup file.

```
Pulls all resource types for the folder (addresses, security rules,
profiles, zones, VPN, deployment, etc.) and writes a timestamped JSON
file. The backup file can be used as input to scm_config_diff and as
the data source for the AS-BUILT report.

Args:
    folder: SCM folder to back up.
    tenant_id: SCM tenant ID (MSSP mode).
    output_dir: Directory to write the backup file (default: ./backups).

Returns:
    Path to the written backup file and a resource count summary.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `output_dir` | `str` | `''` |

### `scm_bpa_assess`

Run Palo Alto Networks Best Practice Assessment checks against live SCM config.

```
Pulls the current configuration from SCM and evaluates it against PAN
best practice checks (security rules, threat prevention profiles, URL
filtering, decryption, zone protection, and logging).

Each finding includes:
- Check ID and severity (critical/high/medium/low)
- Pass/Fail/Warn status
- Affected object names
- Remediation guidance
- NCSC control cross-references

Args:
    folder: SCM folder to assess.
    tenant_id: SCM tenant ID (MSSP mode).
    severity_filter: Filter to a severity level (critical/high/medium/low).
    failed_only: If true, return only failed and warned checks.

Returns:
    JSON-formatted BPA findings.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `severity_filter` | `str` | `''` |
| `failed_only` | `bool` | `False` |

### `scm_ncsc_assess`

Assess SCM configuration against UK NCSC compliance frameworks.

```
Evaluates the live SCM configuration against:
- NCSC CAF v4.0 (Cyber Assessment Framework, August 2025)
- Cyber Essentials v3.2 (firewall controls)
- NCSC 10 Steps to Cyber Security (network security steps)

Returns a control-by-control compliance view showing which NCSC
controls are satisfied, breached, or cannot be assessed.

Args:
    folder: SCM folder to assess.
    tenant_id: SCM tenant ID (MSSP mode).
    framework: Filter to framework — 'caf', 'ce', '10steps', or 'all'.

Returns:
    JSON NCSC compliance view with per-control status.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `framework` | `str` | `'all'` |

### `scm_dspt_assess`

Assess SCM configuration against the NHS DSPT (Data Security and Protection Toolkit).

```
Evaluates live SCM/NGFW configuration against the technology standards
of the NHS England DSPT 2024-25 (v5.1), specifically:

- **Standard 7**: Continuity Planning (config backup and recovery)
- **Standard 8**: Unsupported Systems (PAN-OS currency, patching)
- **Standard 9**: IT Protection (firewall, malware, URL filtering,
  encryption, access control, MFA, audit logging)
- **Standard 10**: Accountable Suppliers (MSSP DPAs, sub-processor assurance)

For each DSPT assertion, the tool reports:
- Compliance status (Compliant / Non-Compliant / Not Assessed)
- Which BPA checks provide the evidence
- An evidence statement ready to paste into the DSPT portal
- DSPT assessment level (Approaching / Meeting / Exceeding Standards)

Standards 1–6 (People and Process) cannot be automated from firewall
config and must be self-assessed within the NHS DSPT portal.

Args:
    folder: SCM folder to assess (e.g. "Shared" or a customer folder).
    tenant_id: SCM tenant ID (MSSP mode). Defaults to active tenant.
    standard: Filter by standard number — '7', '8', '9', '10', or 'all'.
    output_format: 'markdown' (default) or 'json'.
    save_to: Optional file path to save the report (e.g. 'reports/dspt.md').
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `standard` | `str` | `'all'` |
| `output_format` | `str` | `'markdown'` |
| `save_to` | `str` | `''` |

### `scm_iso27001_assess`

Assess SCM/NGFW configuration against ISO 27001:2022 Annex A controls.

```
Maps all 39 BPA checks to 12 automatable Annex A controls across the
technological and organisational domains. Controls requiring non-technical
ISMS evidence (governance, HR, physical) are out of scope and noted
explicitly — this tool covers the firewall-observable subset only.

Controls assessed:
  A.5.14  Information transfer (file blocking, DLP)
  A.5.28  Collection of evidence (logging, SIEM forwarding)
  A.8.7   Protection against malware (AV, WildFire, DNS sec)
  A.8.15  Logging (log forwarding, syslog, deny logging)
  A.8.20  Networks security (DNS sec, URL filter, zone protection)
  A.8.21  Security of network services (TLS decryption)
  A.8.22  Segregation of networks (zones, MFA, HIP, App-ID)
  A.8.23  Web filtering (URL categories, high-risk blocks)
  A.8.24  Use of cryptography (IKEv2, strong IKE/IPSec, PFS)
  A.8.27  Secure system architecture (zero trust, App-ID, no double-any)
  A.8.28  Secure coding (vulnerability protection as compensating control)
  A.8.29  Security testing (HIP patch management as compensating control)

Args:
    folder: SCM folder to assess (e.g. 'Shared', 'All').
    tenant_id: Specific tenant; uses default if omitted.
    clause_filter: 'all' (default), '5' (org controls only),
                   '8' (technological only), or specific control e.g. 'A.8.22'.
    output_format: 'markdown' (default) or 'json'.
    save_to: Optional file path to save the report.

Returns:
    Markdown report or JSON dict string.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `clause_filter` | `str` | `'all'` |
| `output_format` | `str` | `'markdown'` |
| `save_to` | `str` | `''` |

### `scm_decrypt_policy_audit`

Deep-dive SSL/TLS decryption policy audit for a SCM folder.

```
Goes beyond BPA-DEC-001/002 to assess:
- **Profile quality**: TLS version (min ≥ 1.2), weak algorithm flags (3DES,
  RC4, MD5, SHA-1, static RSA key exchange), forward-proxy block settings
  (expired cert, untrusted issuer, unknown cert, unsupported version).
- **Rule coverage**: decrypt vs no-decrypt ratio, zone pairs covered, presence
  of any-any catch-all decrypt rule, disabled rules, rules without a profile.
- **Inbound inspection**: whether inbound SSL inspection rules are configured
  for public-facing services.
- **Gap analysis**: prioritised actionable findings with NCSC CAF (D3.b) and
  DSPT Standard 9 cross-references.
- **Overall verdict**: Adequate / Partial / Insufficient with a concise
  executive summary.

Args:
    folder: SCM folder to audit (e.g. 'Shared', 'All', 'Prisma Access').
    tenant_id: Specific tenant; uses default if omitted.
    output_format: 'markdown' (default) or 'json'.
    save_to: Optional file path to save the report.

Returns:
    Markdown report or JSON dict string.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `output_format` | `str` | `'markdown'` |
| `save_to` | `str` | `''` |

### `scm_audit_report`

Generate a combined BPA + NCSC compliance report for a SCM folder.

```
Produces a full AS-BUILT audit document covering:
- Configuration inventory (addresses, rules, profiles, zones, VPN)
- PAN Best Practice Assessment findings with remediation guidance
- NCSC CAF v4.0 / Cyber Essentials v3.2 / 10 Steps cross-reference
- Prioritised remediation action list

Args:
    folder: SCM folder to assess.
    tenant_id: SCM tenant ID (MSSP mode).
    output_format: 'markdown' or 'json'.
    save_to: Optional file path to write the report to disk.

Returns:
    The full report as a string (Markdown or JSON).
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `output_format` | `str` | `'markdown'` |
| `save_to` | `str` | `''` |

### `scm_asbuilt_report`

Generate a full Prisma SASE AS-IS AS-BUILT document.

```
Pulls live configuration from SCM and produces a structured 9-section
AS-BUILT covering:

  2. Deployed Prisma SASE Architecture — live topology Mermaid diagram,
     management plane, compute locations and egress IP reference
  3. Prisma Access Infrastructure — Remote Networks (branches with IPSec
     tunnels, BGP, QoS), Service Connections (DCs), Mobile Users
     (GlobalProtect portals, IP pools, forwarding profiles)
  4. Prisma SD-WAN — ION inventory template (manual; not in SCM API)
  5. SSE & Zero Trust — threat prevention, SWG, ZTNA security rules
  6. Identity & Posture — authentication profiles, SAML IdPs, HIP checks
  7. Observability — log forwarding profiles, syslog/HTTP destinations
  8. MSSP Service Model — RACI, MACD, ITSM integration, SLA matrix
  9. Appendices — subnet/IP pool tables, public egress IP whitelist
     reference, VPN crypto profiles

Sections that cannot be derived from the SCM API (SD-WAN, ADEM, CDL,
SOAR, CIE) are clearly marked with ⚠️ manual-input placeholders.

Args:
    deployment_type: Deployment model — controls the default SCM folder
        and which sections are active.  Choose one of:
          "Prisma Access" (default) — Prisma SASE/PA tenant;
            folder defaults to "Prisma Access".
          "NGFW"          — SCM-managed Next-Gen Firewall fleet;
            folder defaults to "Prisma Access".
          "SD-WAN Only"   — SD-WAN-only tenant (no PA);
            folder defaults to "All".
    folder: SCM folder to report on.  Leave blank to use the
        deployment_type default ("Prisma Access" for PA/NGFW,
        "All" for SD-WAN Only).
    tenant_id: SCM tenant ID (MSSP mode).
    customer_name: Customer name shown in the document header.
    mssp_name: MSSP name shown in the document header.
    doc_version: Document version string (e.g. "1.0").
    output_format: 'markdown' (default) or 'docx' (requires pandoc).
    include_sdwan: If True, pull live SD-WAN data (sites, elements,
                   WAN interfaces, policies) using the same credentials.
                   Fills §4 with real data instead of placeholders.
    save_to: Optional file path to write the report to disk.
             For docx format defaults to '<customer_name>-asbuilt.docx'
             if not specified.
    include_extended: If True, also pull CASB/DLP profiles, ZTNA
                      Connector inventory, and Prisma Browser config.
                      Adds extra API calls — only enable when those
                      sections are needed and the tenant has the licences.
    include_insights: If True, query the Prisma Access Insights v3.0 API
                      for live operational data: RN/SC tunnel status,
                      bandwidth consumption, connected mobile user count,
                      and active alerts. Adds §3.1.2, §3.2.1, §3.3.7,
                      and §3.5 to the AS-BUILT.
    insights_region:  Prisma Access region for the X-PANW-Region header
                      used by the Insights API (default: "eu").
                      Common values: "eu", "us", "uk", "sg", "au".
    include_adem:     If True, query the Autonomous DEM Telemetry API for
                      live application experience scores (last 3 days) and
                      aggregate agent scores. Populates §7.1 with a scored
                      app table instead of the manual-input placeholder.
                      Uses the same SCM OAuth token — no extra credentials.
    enrich_wan_ips:   If True, reverse-look-up each public WAN IP (ISP,
                      ASN, geolocation) and add ISP/Geo/Drift columns to
                      the §4.2.1 SD-WAN and §3.4.7 NGFW WAN IP tables.
                      Sends tenant public IPs to the configured
                      IP-intelligence provider (see ip_enrichment_provider
                      setting) — opt-in for that reason. Results are
                      disk-cached 30 days, so re-runs cost no lookups.

Returns:
    Job ID string. Call scm_asbuilt_result(job_id) once extraction completes.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `deployment_type` | `str` | `'Prisma Access'` |
| `folder` | `str` | `''` |
| `tenant_id` | `str` | `''` |
| `customer_name` | `str` | `''` |
| `mssp_name` | `str` | `'MSSP'` |
| `doc_version` | `str` | `'1.0'` |
| `include_sdwan` | `bool` | `False` |
| `include_extended` | `bool` | `False` |
| `include_insights` | `bool` | `False` |
| `insights_region` | `str` | `'eu'` |
| `include_adem` | `bool` | `False` |
| `enrich_wan_ips` | `bool` | `False` |

### `scm_asbuilt_result`

Retrieve a completed AS-BUILT report started by scm_asbuilt_report.

```
Call this after scm_asbuilt_report returns a job ID. Extraction typically
completes within 2–4 minutes. If still running, a status message is returned
— simply call again after another minute.

Args:
    job_id: Job ID returned by scm_asbuilt_report.
    save_to: Optional file path to write the completed report.
    output_format: 'markdown' (default) or 'docx' (requires pandoc).

Returns:
    The full Markdown AS-BUILT, a save-path confirmation, or a status
    message if still running.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `job_id` | `str` | `—` |
| `save_to` | `str` | `''` |
| `output_format` | `str` | `'markdown'` |

### `scm_config_diff`

Compare two SCM config backup files and report differences.

```
Useful for change auditing — run a backup before and after a change
window to produce a structured diff of what was added, removed, or
modified across all resource types.

Args:
    backup_file_a: Path to the baseline backup JSON file.
    backup_file_b: Path to the comparison backup JSON file.

Returns:
    JSON diff report showing added, removed, and changed resources.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `backup_file_a` | `str` | `—` |
| `backup_file_b` | `str` | `—` |

### `scm_config_clone`

Clone a SCM config backup into a new folder or tenant.

```
Loads a JSON backup created by scm_config_backup, sanitises every
object (strips system fields, rewrites the folder, scrubs PSKs), then
pushes it to the target folder in dependency order:

  Tags → Addresses → Groups → Security profiles → Log profiles →
  Zones → Rules (pre, post, NAT, decryption) → Deployment (optional)

Typical use-cases
-----------------
- MSSP golden-config template → new customer tenant (speed up onboarding)
- MSSP takeover migration → move config from old MSSP to new tenant
- POV → Prod promotion (clone lab folder to production folder)
- Multi-site rollout (one branch config → N sites with same structure)

PSK safety
----------
Pre-shared keys in IKE gateways are ALWAYS replaced with
CHANGEME_<gateway-name>. The report lists every gateway that needs
a real PSK set before committing.

Args:
    source_backup_file: Path to a JSON backup from scm_config_backup.
    target_folder: Destination SCM folder name.
    target_tenant_id: Destination tenant (empty = same tenant as server default).
    name_prefix: Prefix prepended to every object name (e.g. "CUST1_").
                 Useful when cloning into a shared folder.
    anonymise_ips: Replace all IPv4 literals with {{IP_N}} template
                   variables. Use when sharing configs as templates.
    include_deployment: Also clone IKE gateways, IPSec tunnels,
                        Remote Networks, and Service Connections.
                        These go into fixed SCM folders (Remote Networks,
                        Service Connections) regardless of target_folder.
    skip_rules: Omit all security, NAT, decryption, and app-override
                rules. Useful when cloning only the object library.
    on_conflict: What to do if an object with the same name already
                 exists in the target — 'skip' (default) or 'overwrite'.
    dry_run: If True (default), preview what would be created without
             making any API calls. Set to False to execute the push.
    save_to: Optional file path to write the clone report.

Returns:
    Markdown clone report showing per-object status and PSK warnings.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `source_backup_file` | `str` | `—` |
| `target_folder` | `str` | `—` |
| `target_tenant_id` | `str` | `''` |
| `name_prefix` | `str` | `''` |
| `anonymise_ips` | `bool` | `False` |
| `include_deployment` | `bool` | `False` |
| `skip_rules` | `bool` | `False` |
| `on_conflict` | `str` | `'skip'` |
| `dry_run` | `bool` | `True` |
| `save_to` | `str` | `''` |

---

## NCSC Baseline

_Apply NCSC-aligned security baseline, attach profiles, gap analysis._

### `scm_apply_ncsc_baseline`

Create NCSC-compliant security profiles and deny-all rule in a SCM folder.

```
Creates:
  - Anti-spyware profile with cloud inline analysis + MICA C2 detectors
  - Vulnerability protection profile (block critical/high, alert medium)
  - WildFire antivirus profile (all files, both directions)
  - URL access profile (block malware/C2/phishing categories)
  - Log forwarding profile (traffic/threat/wildfire/url/auth → Cortex Data Lake)
  - Explicit deny-all security rule with logging
  - NCSC-Compliant tag

NCSC compliance mapping:
  CAF v4.0  — C3 Identity/Access, C4 Data security, C5 Security monitoring
  CE v3.2   — Malware protection, Patch management, Network monitoring
  10 Steps  — Network security, Malware defences, Monitoring

Args:
    folder: Target SCM folder (e.g. "Shared" or a tenant folder name).
    dry_run: If True (default) show what WOULD be created without writing.
    syslog_profile: Optional syslog server profile name to add to log forwarding.
    overwrite_existing: If True, skip objects that already exist silently.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `dry_run` | `bool` | `True` |
| `syslog_profile` | `str` | `''` |
| `overwrite_existing` | `bool` | `False` |
| `tenant_id` | `str` | `''` |

### `scm_create_ncsc_snippet`

Create an SCM snippet containing NCSC-compliant security profiles.

```
Creates a named snippet container and populates it with:
  - Anti-spyware profile (block C2 / critical+high spyware, MICA inline)
  - Vulnerability protection profile (block critical/high CVEs)
  - WildFire antivirus profile (all files, both directions, public cloud)
  - URL access profile (block malware/C2/phishing categories)
  - Log forwarding profile (traffic/threat/wildfire/url/auth → Cortex Data Lake)
  - NCSC-Compliant tag

Snippets are reusable configuration bundles that can be pushed to multiple
tenants or folders — they do NOT contain security rules (rules must be created
separately in a folder rulebase).

NCSC compliance mapping:
  CAF v4.0  — C3 Identity/Access, C4 Data security, C5 Security monitoring
  CE v3.2   — Malware protection, Patch management, Network monitoring
  10 Steps  — Network security, Malware defences, Monitoring

Args:
    snippet_name: Name of the SCM snippet to create (default: "NCSC-Compliance").
    dry_run: If True (default) show what WOULD be created without writing.
    syslog_profile: Optional syslog server profile name to add to log forwarding.
    description: Description for the snippet container.
    tenant_id: Tenant to target (default: first loaded tenant).
```

| Parameter | Type | Default |
|-----------|------|---------|
| `snippet_name` | `str` | `'NCSC-Compliance'` |
| `dry_run` | `bool` | `True` |
| `syslog_profile` | `str` | `''` |
| `description` | `str` | `'NCSC CAF v4.0 / CE v3.2 compliance baseline — managed by scm-mcp-mssp'` |
| `tenant_id` | `str` | `''` |

### `scm_create_nist_snippet`

Create an SCM snippet containing NIST-compliant security profiles.

```
Creates a named snippet container and populates it with:
  - Anti-spyware profile (C2 detection, block critical+high spyware)
  - Vulnerability protection profile (block critical/high CVEs, alert medium)
  - WildFire antivirus profile (all files, both directions, public cloud)
  - URL access profile (block malware/C2/phishing categories)
  - Log forwarding profile (traffic/threat/wildfire/url/auth → Cortex Data Lake)
  - NIST-Compliant tag

Snippets are reusable configuration bundles — they do NOT contain security rules
(add deny-all and rule tuning separately via scm_apply_ncsc_baseline).

NIST compliance mapping:
  CSF v2.0   — GV.OC, PR.PS, PR.AA, DE.CM, DE.AE, RS.AN
  SP 800-53  — SI-2 Flaw Remediation, SI-3 Malware Protection, SI-4 Monitoring,
               RA-5 Vulnerability Monitoring, AU-2/AU-12 Audit Logging,
               SC-7 Boundary Protection, AC-3 Access Enforcement
  SP 800-171 — 3.14 System and Information Integrity

Args:
    snippet_name: Name of the SCM snippet to create (default: "NIST-Compliance").
    dry_run: If True (default) show what WOULD be created without writing.
    syslog_profile: Optional syslog server profile name to add to log forwarding.
    description: Description for the snippet container.
    tenant_id: Tenant to target (default: first loaded tenant).
```

| Parameter | Type | Default |
|-----------|------|---------|
| `snippet_name` | `str` | `'NIST-Compliance'` |
| `dry_run` | `bool` | `True` |
| `syslog_profile` | `str` | `''` |
| `description` | `str` | `'NIST CSF v2.0 / SP 800-53 Rev 5 compliance baseline — managed by scm-mcp-mssp'` |
| `tenant_id` | `str` | `''` |

### `scm_attach_ncsc_profiles`

Create the NCSC-Baseline security profile group and attach it to all allow rules in the folder that are missing profiles or log forwarding.

```
Steps:
  1. Create (or verify) the 'NCSC-Baseline' profile group referencing the
     four NCSC baseline profiles
  2. For every allow rule in the folder that has no profile_setting or
     no log_setting, update it with:
       - profile_setting.group = [profile_group_name]
       - log_setting = 'NCSC-Baseline-Logging'
       - log_end = True

Only rules stored in an editable folder (not 'All') are updated.
Rules from folder='All' are read-only predefined rules that cannot be changed.

Args:
    folder: SCM folder to search for rules (e.g. 'Prisma Access').
    dry_run: If True (default) show what WOULD be changed without writing.
    profile_group_name: Name of the profile group to create/use.
    skip_already_profiled: If True (default), skip rules that already have
                           a profile group set.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `dry_run` | `bool` | `True` |
| `profile_group_name` | `str` | `'NCSC-Baseline'` |
| `skip_already_profiled` | `bool` | `True` |
| `tenant_id` | `str` | `''` |

### `scm_ncsc_gap`

Compare live SCM config against the NCSC baseline and report compliance gaps.

```
Checks:
  - Every allow rule has a security profile group and log forwarding
  - An explicit deny-all rule exists at the bottom of the rulebase
  - Anti-spyware profiles have cloud inline analysis and MICA C2 detectors
  - Log forwarding profile covers traffic/threat/wildfire/url log types
  - NCSC baseline profile objects exist in the folder

Maps gaps to: CAF v4.0, CE v3.2, NCSC 10 Steps, NSF controls.

Args:
    folder: SCM folder to inspect.
    position: Security rule position — "pre", "post", or "both".
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `position` | `str` | `'pre'` |
| `tenant_id` | `str` | `''` |

### `scm_nist_gap`

Compare live SCM config against the NIST baseline and report compliance gaps.

```
Checks:
  - Every allow rule has a security profile group and log forwarding
    (NIST CSF PR.AC-5, SP 800-53 AC-3, SC-7)
  - An explicit deny-all rule exists at the bottom of the rulebase
    (SP 800-53 SC-7 Boundary Protection)
  - Anti-spyware profiles have cloud inline analysis and C2 detection
    (SP 800-53 SI-3 Malware Protection, SI-4 System Monitoring)
  - Log forwarding profile covers traffic/threat/wildfire/url log types
    (SP 800-53 AU-2 / AU-12 Audit Logging)
  - NIST baseline profile objects exist in the folder
    (SI-2 Flaw Remediation, RA-5 Vulnerability Monitoring, SP 800-171 3.14)

Maps gaps to: NIST CSF v2.0 (GV/ID/PR/DE/RS), SP 800-53 Rev 5, SP 800-171.

Args:
    folder: SCM folder to inspect.
    position: Security rule position — "pre", "post", or "both".
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `position` | `str` | `'pre'` |
| `tenant_id` | `str` | `''` |

---

## Enterprise DLP

_Enterprise DLP profile listing, backup, and restore._

### `dlp_enterprise_list`

List Enterprise DLP data patterns and data profiles for a tenant.

```
Queries the PAN Enterprise DLP API (api.dlp.paloaltonetworks.com)
which covers ML-based DLP patterns used by Prisma SaaS Security and
Cloud SWG — distinct from inline SCM data-filtering-profiles.

If company_id is omitted the tool auto-discovers it via
GET /v1/config/companies.

Args:
    tenant_id:  SCM tenant ID (MSSP mode). Omit for default tenant.
    company_id: Enterprise DLP company ID. Auto-discovered if blank.

Returns:
    Markdown summary of Enterprise DLP data patterns and profiles.

Ref: https://pan.dev/dlp/api/
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `company_id` | `str` | `''` |

### `dlp_backup`

Export full DLP configuration as a JSON backup for cross-tenant redeployment.

```
Exports two layers of DLP config:

  SCM DLP (inline):
    - Data filtering profiles  (/config/v1/data-filtering-profiles)
    - Data objects             (/config/v1/data-objects)

  Enterprise DLP (ML-based, optional):
    - Data patterns            (api.dlp.paloaltonetworks.com data-patterns)
    - Data profiles            (api.dlp.paloaltonetworks.com data-profiles)

The returned JSON can be passed directly to `dlp_restore` to provision
an identical DLP configuration on another tenant/folder.

Args:
    folder:             SCM folder to export inline DLP from (default: All).
    tenant_id:          Source tenant ID (MSSP mode).
    company_id:         Enterprise DLP company ID. Auto-discovered if blank.
    include_enterprise: Include Enterprise DLP patterns and profiles (default: True).

Returns:
    JSON backup payload (pretty-printed).

Ref: https://pan.dev/dlp/api/
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'All'` |
| `tenant_id` | `str` | `''` |
| `company_id` | `str` | `''` |
| `include_enterprise` | `bool` | `True` |

### `dlp_restore`

Restore a DLP backup onto a target tenant/folder.

```
Accepts a JSON backup produced by `dlp_backup` and provisions the
contained DLP objects on the target tenant:

  1. SCM data objects             → POST /config/v1/data-objects
  2. SCM data filtering profiles  → POST /config/v1/data-filtering-profiles
  3. Enterprise DLP data patterns → POST /v1/config/companies/{cid}/data-patterns
  4. Enterprise DLP data profiles → POST /v1/config/companies/{cid}/data-profiles

Objects are skipped if a resource with the same name already exists
(HTTP 409 / 400 duplicate-name response).

Args:
    backup_json:   JSON string produced by `dlp_backup`.
    target_folder: SCM folder to restore inline DLP objects into.
    tenant_id:     Target tenant ID (MSSP mode).
    company_id:    Enterprise DLP company ID for the target tenant.
                   Auto-discovered if blank.
    dry_run:       If True (default), only report what would be created.
                   Set to False to apply changes.

Returns:
    Markdown restore report listing created / skipped / failed objects.

Ref: https://pan.dev/dlp/api/
```

| Parameter | Type | Default |
|-----------|------|---------|
| `backup_json` | `str` | `—` |
| `target_folder` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `company_id` | `str` | `''` |
| `dry_run` | `bool` | `True` |

---

## MSSP Multi-Tenant

_Tier assessment, onboarding, dashboard, licensing, CDL, CASB, ZTNA, Browser, NGFW, AIRS._

### `mssp_tier_assess`

Score a tenant folder against its contracted MSSP service tier.

```
Pulls live SCM configuration, runs all BPA checks, then scores results
against the tier requirements:
  Bronze — Critical checks must pass (CE baseline)
  Silver — Critical + High checks must pass (CE Plus)
  Gold   — All checks must pass (CAF v4.0)

Args:
    folder: SCM folder to assess.
    tier: Service tier to assess against (gold/silver/bronze).
          If omitted, uses the tenant's configured tier.
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    JSON tier compliance result with breach list and score percentage.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tier` | `str` | `''` |
| `tenant_id` | `str` | `''` |

### `mssp_tier_report`

Generate a Markdown tier compliance report for a customer folder.

```
Produces a customer-facing document showing:
- Service tier description and included features
- Compliance score against tier requirements
- Breach findings with remediation steps
- Advisory findings (higher tier, for upsell context)
- Upgrade path to next tier

Args:
    folder: SCM folder to assess.
    tier: Service tier (gold/silver/bronze).
    tenant_id: SCM tenant ID.
    save_to: Optional file path to write the report.

Returns:
    Markdown compliance report.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tier` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `save_to` | `str` | `''` |

### `mssp_upgrade_path`

Show what's needed to upgrade a tenant from one tier to another.

```
Analyses the live configuration against the target tier requirements
and returns:
- Blocking findings that must be resolved before upgrading
- Additional NCSC controls that become mandatory
- New SCM snippets that need to be applied
- New features included in the target tier

Args:
    folder: SCM folder to assess.
    from_tier: Current contracted tier (gold/silver/bronze).
    to_tier: Target tier (gold/silver/bronze).
    tenant_id: SCM tenant ID.

Returns:
    JSON upgrade gap analysis.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `from_tier` | `str` | `—` |
| `to_tier` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `mssp_onboard_tenant`

Onboard a new customer tenant with the correct tier snippet set.

```
Checks whether required tier snippets exist in SCM and reports which
are present vs missing. With dry_run=False, associates existing snippets
with the target folder.

Args:
    folder: Customer SCM folder name.
    tier: Service tier to apply (gold/silver/bronze).
    tenant_id: SCM tenant ID.
    create_folder: If True, create the folder if it doesn't exist.
    dry_run: If True (default), report actions without executing.
             Set to False to apply snippet associations.

Returns:
    Onboarding plan or execution result with snippet status.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `tier` | `str` | `—` |
| `tenant_id` | `str` | `''` |
| `create_folder` | `bool` | `False` |
| `dry_run` | `bool` | `True` |

### `mssp_tenant_dashboard`

Show a summary dashboard of all loaded MSSP tenants and their tier status.

```
Lists every tenant currently cached in the server, showing their
configured tier, folder, label, and service term.

Args:
    tenant_id: Not used for filtering — returns all loaded tenants.

Returns:
    Markdown dashboard of all tenants.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `mssp_snippet_catalogue`

List MSSP tier snippet templates and their content specifications.

```
Shows what each tier's SCM snippets should contain, enabling
engineers to create the correct snippets in SCM before onboarding.

Args:
    tier: Filter to a specific tier (gold/silver/bronze) or omit for all.

Returns:
    Markdown catalogue of snippet templates by tier.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tier` | `str` | `''` |

### `scm_license_info`

List all Prisma SASE subscription licences for a tenant, with expiry dates.

```
Calls the Palo Alto Networks Subscription Service API
(GET /subscription/v1/licenses) using the tenant's existing OAuth session.
Returns a Markdown table grouped by product, showing SKU, quantity,
consumed seats, expiry date, and status (active / expired / expiring soon).

Args:
    tenant_id: SCM tenant ID.  Omit to use the default tenant.

Returns:
    Markdown licence summary table.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `scm_mobile_user_stats`

Show Prisma Access mobile user allocation and current logged-in user count.

```
Uses the Prisma Access Insights API to retrieve live connected user counts,
plus bandwidth allocation from SCM config.

Args:
    tenant_id: SCM tenant ID. Omit to use the default tenant.
    region: Prisma Access Insights region for X-PANW-Region header
            (e.g. 'eu' for Europe, 'us' for US). Default: 'eu'.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `region` | `str` | `'eu'` |

### `scm_discover_tenants`

Discover all managed sub-tenants visible to the authenticated SP/super-user account.

```
Calls the Prisma SASE Tenancy API (GET /tenancy/v1/tenants) and the IAM API
(GET /iam/v1/access-policies, /iam/v1/service-accounts) to return:
- TSG ID, display name, and status for every managed sub-tenant
- Admin users and their assigned roles per tenant
- Service accounts registered in this tenant

Requires SP-level credentials (super-user or Tenant Management IAM role).
Returns a summary table for tenant-level credentials (may show only the
current tenant).

Args:
    tenant_id: SCM tenant ID. Omit to use the default tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `scm_dlp_list`

List DLP data-filtering profiles and data objects configured in SCM. Uses the SCM Config REST API (/config/v1/data-filtering-profiles and /config/v1/data-objects) — these are not exposed via the pan-scm-sdk.

```
Args:
    folder:    SCM folder scope (default: All).
    tenant_id: Tenant ID. Omit to use the default tenant.

Returns:
    Markdown summary of DLP profiles and data objects.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'All'` |
| `tenant_id` | `str` | `''` |

### `scm_casb_list`

List CASB SaaS tenant restrictions configured in SCM. Uses /config/v1/saas-tenant-restrictions (SCM Config REST API).

```
Args:
    folder:    SCM folder scope (default: All).
    tenant_id: Tenant ID. Omit to use the default tenant.

Returns:
    Markdown summary of SaaS tenant restriction policies.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'All'` |
| `tenant_id` | `str` | `''` |

### `scm_ztna_connector_list`

List ZTNA Connector infrastructure (connectors and connector groups). Uses the ZTNA Connector API (/sse/connector/v2.0/api/). Returns an empty result if ZTNA Connector is not licensed/enabled.

```
Args:
    tenant_id: Tenant ID. Omit to use the default tenant.

Returns:
    Markdown summary of ZTNA connectors and groups.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `scm_browser_list`

List Prisma Browser (Remote Browser Isolation / RBI) configuration. Uses the Prisma Browser Management API (/seb/api/v1/). Covers: users, devices, device groups, user groups, applications, application groups, plugins, and user requests. Returns an empty result if Prisma Browser is not licensed.

```
Args:
    tenant_id: Tenant ID. Omit to use the default tenant.

Returns:
    Markdown summary of Prisma Browser configuration.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `mssp_tier_comparison`

Return a side-by-side comparison of Gold / Silver / Bronze tiers.

```
Useful for sales and customer conversations — shows what each tier
includes, which NCSC frameworks it covers, and the check requirements.

Returns:
    Markdown comparison table.
```

### `scm_ngfw_device_list`

List NGFW managed devices onboarded to Strata Cloud Manager.

```
Returns device inventory including model, serial number, software version,
HA state, connection status, folder assignment, and registration authcode
(auth_key) where available.

Args:
    folder:    SCM folder to query (default: ngfw-shared).
    tenant_id: Tenant ID. Omit to use the default tenant.

Returns:
    Markdown table of NGFW devices, or a message if none are onboarded.

Ref: https://pan.dev/scm/api/config/ngfw/setup/list-devices/
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'ngfw-shared'` |
| `tenant_id` | `str` | `''` |

### `scm_airs_list`

List Prisma AIRS (AI Runtime Security) configuration for a tenant.

```
Queries the AIRS management API for:
- Customer Applications — AI apps registered for inline API inspection
- AI Security Profiles — threat detection profile configurations
- Deployment Profiles — how AIRS is deployed (inline, async, etc.)

Returns 'not licensed' if AIRS is not activated for this tenant.

Args:
    tenant_id: Tenant ID. Omit to use the default tenant.

Returns:
    Markdown summary of AIRS configuration.

Ref: https://pan.dev/prisma-airs/api/airuntimesecurity/prismaairsmanagementapi/
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

---

## Prisma SD-WAN

_Sites, elements, WAN interfaces/networks, path groups, policies and rules, topology, events/alarms, audit log, software status, link health._

### `sdwan_list_sites`

List Prisma SD-WAN sites (branches, data centres, hub sites).

```
Returns name, address, geo location (latitude/longitude), site type
(branch/dc/hub), element count, admin state, and WAN interface count
for each site.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Optional specific site ID to fetch.

Returns:
    JSON array of site objects.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |

### `sdwan_list_elements`

List Prisma SD-WAN ION elements (physical or virtual appliances).

```
Returns model, serial, software version, site assignment, HA role,
and connected state for each element.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Filter to a specific site ID.
    element_id: Fetch a specific element by ID.

Returns:
    JSON array of element objects.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `element_id` | `str` | `''` |

### `sdwan_list_wan_interfaces`

List Prisma SD-WAN WAN interfaces for a site or element.

```
Returns interface name, type (public/private), circuit, bandwidth,
network label, and link quality for each WAN interface.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Required — site ID to query.
    element_id: Optional — filter to a specific element.

Returns:
    JSON array of WAN interface objects.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `element_id` | `str` | `''` |

### `sdwan_wan_ip_summary`

Report the live public/private WAN IP address bound to each ION element.

```
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
default ip-api.com) — hence opt-in, never on by default. Lookups are
cached on disk for 30 days, so repeat runs stay off provider rate
limits. Enriched records then get advisory `drift` flags: observed
ISP vs the circuit's configured WAN network / circuit name
(`wan_network`/`circuit_name`, both now on every record), and IP
geolocation vs the site's configured coordinates (>500 km flags).

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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `enrich` | `bool` | `False` |

### `sdwan_list_wan_networks`

List Prisma SD-WAN WAN networks (ISP circuit definitions).

```
Returns network name, type (publicwan/privatewan/lte), and provider info.

Args:
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    JSON array of WAN network objects.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `sdwan_list_path_groups`

List Prisma SD-WAN path groups (circuit groupings for policy selection).

```
Args:
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    JSON array of path group objects.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `sdwan_list_policies`

List Prisma SD-WAN policy sets.

```
Args:
    tenant_id: SCM tenant ID (MSSP mode).
    policy_type: 'network' (path selection), 'priority' (QoS),
                 'security' (NGFW), or 'all'.

Returns:
    JSON policy set summary.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `policy_type` | `str` | `'network'` |

### `sdwan_list_clusters`

List Prisma SD-WAN hub and spoke clusters (HA topology).

```
Args:
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    JSON summary of hub clusters and spoke clusters.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `sdwan_list_bgp`

List Prisma SD-WAN BGP configurations and peer status.

```
Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Filter to a specific site.
    element_id: Filter to a specific element.

Returns:
    JSON BGP configs and peer summary.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `element_id` | `str` | `''` |

### `sdwan_topology_diagram`

Generate a Mermaid VPN overlay topology diagram for Prisma SD-WAN.

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `save_to` | `str` | `''` |

### `sdwan_debug_topology`

Return the raw JSON from POST /sdwan/v3.6/api/topology for one site.

```
Used to inspect the actual API response structure so field names can
be verified against what build_topology expects.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Site ID to query. If omitted, uses the first site found.

Returns:
    Raw JSON response (first 8 KB) plus the VPN links query result.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |

### `sdwan_topology`

Generate a full Prisma SD-WAN topology summary.

```
Pulls sites, elements, WAN networks, hub/spoke clusters, and policy
sets to produce a single structured overview of the SD-WAN deployment.

Args:
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    JSON topology summary with site and element inventory.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `sdwan_site_map`

Generate an interactive HTML map of SD-WAN sites from their geo data.

```
Plots every site that has configured coordinates (see
sdwan_list_sites `location`) on a Leaflet/OpenStreetMap map — DC/hub
sites in red, branches in blue — with a popup per site showing its
role, street address, ION elements (name, model, connected state),
and WAN circuits. Complements the Mermaid topology diagram (which has
no geographic layout) for AS-BUILT §4 and customer workshops.

The generated file is standalone HTML but loads the Leaflet library
and OSM map tiles from the internet when opened — tile requests
reveal the mapped area to the tile server, so treat the file like
the site list itself.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    save_to: Output path (default: sdwan-site-map-<tenant>.html in
             the current directory).

Returns:
    Path of the written HTML file plus a summary of mapped/skipped
    sites.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `save_to` | `str` | `''` |

### `sdwan_events`

List Prisma SD-WAN events (alarms and alerts) with a severity summary.

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `hours` | `int` | `24` |
| `category` | `str` | `'all'` |
| `severity` | `str` | `''` |
| `site_id` | `str` | `''` |
| `code` | `str` | `''` |
| `include_cleared` | `bool` | `True` |
| `max_events` | `int` | `50` |

### `sdwan_audit_logs`

List Prisma SD-WAN audit-log entries (who changed what, and when).

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `hours` | `int` | `24` |
| `limit` | `int` | `50` |

### `sdwan_software_status`

Report ION software versions, pending upgrades, and upgrade jobs.

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `element_id` | `str` | `''` |

### `sdwan_policy_rules`

List Prisma SD-WAN policy sets, stacks, and the rules inside them.

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `policy_type` | `str` | `'path'` |
| `policy_set_id` | `str` | `''` |

### `sdwan_link_health`

Report link quality (latency, jitter, MOS) and bandwidth for a site.

```
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
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `hours` | `int` | `3` |
| `interval` | `str` | `'5min'` |
| `include_bandwidth` | `bool` | `True` |
| `max_paths` | `int` | `6` |

### `sdwan_flows`

Top talkers for a site from the SD-WAN flow log.

```
Queries the flow records the site's IONs reported over the last
`hours` hours and aggregates them client-side into top sources, top
destinations, and top applications by bytes, plus a per-path-type
byte breakdown and a count of dropped flows (flow_action=flow_drop).
Application IDs are resolved to display names via appdefs.

The flow monitor accepts exactly one site per request; an idle site
legitimately returns zero flows.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Required — site to report on (see sdwan_list_sites).
    hours: Look-back window in hours (default 1).
    top: How many entries per top-talker list (default 10).
    max_flows: Flow records to request from the API (default 500).

Returns:
    JSON with `total_flows`, `dropped_flows`, `top_sources`,
    `top_destinations`, `top_applications`, and `path_types`.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `hours` | `int` | `1` |
| `top` | `int` | `10` |
| `max_flows` | `int` | `500` |

### `sdwan_app_health`

Tenant/site application health: healthscore buckets and top-N.

```
Reports three views over the last `hours` hours:
- `healthscore`: how many sites, circuits, and anynet links fall in
  each health bucket (good/fair/poor/others).
- `top_applications`: top 10 apps by `basis` (default traffic
  volume; media bases like egress_audio_mos target voice/video),
  scoped to `site_id` when given, app IDs resolved to names.
- `top_sites`: top 10 sites by the same basis (tenant-wide view,
  only included when site_id is not set).
Per-app healthscore detail is also queried; many tenants return no
datapoints unless app monitoring is enabled.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    site_id: Optional site to scope the top-apps view to.
    hours: Look-back window in hours (default 24).
    basis: Top-N ranking basis (traffic_volume, tcp_flow, udp_flow,
        transaction_failure, or media bases like egress_audio_mos).

Returns:
    JSON with `healthscore`, `top_applications`, `top_sites`, and
    `app_healthscores`.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `site_id` | `str` | `''` |
| `hours` | `int` | `24` |
| `basis` | `str` | `'traffic_volume'` |

### `sdwan_cellular_status`

Status of cellular (LTE/5G) modules across ION elements.

```
Joins each configured cellular module to its live status: modem
state, carrier, radio technology, signal strength, network/packet
registration, active SIM and per-slot SIM state, and active
firmware. Elements without cellular modules simply don't appear.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    element_id: Optional — only modules on this element.

Returns:
    JSON array of cellular module objects with element/site names.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `element_id` | `str` | `''` |

---

## Operational Visibility

_Certificate scan/lifecycle, TLS profile manager, licence forecast, tenant NOC dashboard, SPN bandwidth, GP sessions, device/user summaries, SDK & spec drift update check._

### `scm_cert_scan`

Scan all SCM certificate objects and flag anything expiring soon.

```
Fetches certificates from the SCM config store via the certificates
REST API and checks each against today's date. Covers CA certificates,
SSL/TLS inspection certs, IKE certs, and SAML signing certificates
stored as SCM objects.

Also lists any IKE gateways configured to use certificate
authentication (rather than pre-shared keys), so the operator can
cross-reference gateway names against the certificate table above.

Args:
    folder: Primary SCM folder to scan (default: Shared).
    tenant_id: SCM tenant ID (MSSP mode). Leave empty for the active
               single-tenant client.
    warn_days: Highlight certs expiring within this many days
               (default 90). CRITICAL threshold is always 30 days,
               WARNING is always 60 days.
    all_folders: Also scan Remote Networks, Mobile Users, Service
                 Connections folders (default: True).

Returns:
    Markdown report: status summary, full cert table sorted by expiry,
    and IKE gateway cert-auth cross-reference.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'Shared'` |
| `tenant_id` | `str` | `''` |
| `warn_days` | `int` | `90` |
| `all_folders` | `bool` | `True` |

### `scm_cert_lifecycle`

Multi-tenant TLS certificate lifecycle dashboard.

```
Sweeps all SCM certificate objects across one or all MSSP tenants.
Identifies SSL inspection CA certificates — these are the most critical
to monitor because expiry silently disables SSL decryption with no
user-visible error. Produces per-tenant expiry detail and a cross-tenant
summary table for the MSSP morning brief.

SSL Inspection CA detection: any CA-type certificate (ca=true) whose
name or CN contains 'ssl', 'inspect', 'decrypt', 'forward-proxy',
or 'intercept' is flagged as a probable SSL inspection CA.

Args:
    tenant_id: SCM tenant ID. Leave empty for the active tenant.
    warn_days: Days threshold for CAUTION status (default 90).
    all_tenants: If True (MSSP mode), sweep all configured MSSP tenants.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `warn_days` | `int` | `90` |
| `all_tenants` | `bool` | `False` |

### `scm_cert_import`

Import a PEM certificate into an SCM tenant folder.

```
Uploads a certificate object to the SCM config store. Use this to
deploy a new SSL inspection CA, replace an expiring cert, or add
a trusted root CA. Does not import private keys — use the SCM UI
for PKCS12 imports that include private keys.

After import, run scm_commit to activate the new certificate.

Args:
    name: Certificate object name in SCM (e.g. "SSL-Inspect-CA-2026").
    pem: PEM-encoded certificate text (the full -----BEGIN CERTIFICATE----- block).
    folder: SCM folder to import into (default: Shared).
    is_ca: Mark this certificate as a CA certificate (default False).
    tenant_id: SCM tenant ID. Defaults to the configured default tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `pem` | `str` | `—` |
| `folder` | `str` | `'Shared'` |
| `is_ca` | `bool` | `False` |
| `tenant_id` | `str` | `''` |

### `scm_tls_profile_manager`

List or create TLS service profiles for SSL inspection configuration.

```
TLS service profiles define which TLS versions and cipher suites are
permitted in SSL Forward Proxy inspection. They are referenced by
decryption profiles, which are in turn applied by decryption rules.

action='list'   — list all TLS service profiles for this tenant
action='create' — create a new profile (requires name parameter)

Created profiles default to TLS 1.2 minimum, TLS 1.3 maximum —
the NCSC/CE-recommended baseline that blocks legacy TLS.

Args:
    action: 'list' or 'create'.
    name: Profile name (required for create).
    min_version: Minimum TLS version ('tls1-2' or 'tls1-3'). Default: 'tls1-2'.
    max_version: Maximum TLS version ('tls1-2' or 'tls1-3'). Default: 'tls1-3'.
    cert_profile: Optional certificate profile name for client cert validation.
    folder: SCM folder (default: Shared).
    tenant_id: SCM tenant ID. Defaults to the configured default tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `action` | `str` | `'list'` |
| `name` | `str` | `''` |
| `min_version` | `str` | `'tls1-2'` |
| `max_version` | `str` | `'tls1-3'` |
| `cert_profile` | `str` | `''` |
| `folder` | `str` | `'Shared'` |
| `tenant_id` | `str` | `''` |

### `scm_licence_forecast`

Forecast licence expiry dates and seat utilisation.

```
Pulls subscription licence data from the PAN Subscription Service API
and groups entries by product (app_id), reporting the earliest expiry
per product and seat consumption. Useful for proactive renewals and
to catch oversubscribed licence pools before users are impacted.

Seat utilisation is calculated as:
    consumed = purchased_size − remaining_size
    % used   = consumed / purchased_size × 100

Args:
    tenant_id: SCM tenant ID (MSSP mode). Leave empty for the active
               single-tenant client.
    warn_days: Flag licences expiring within this many days (default 90).
               CRITICAL is always <30 days, WARNING is always <60 days.
    all_tenants: If True (MSSP mode), scan every configured tenant and
                 produce a combined forecast. Overrides tenant_id.

Returns:
    Markdown table(s) with expiry status, days remaining, and
    seat utilisation per product per tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `warn_days` | `int` | `90` |
| `all_tenants` | `bool` | `False` |

### `scm_tenant_dashboard`

Multi-tenant NOC health dashboard — traffic-light overview of all tenants.

```
Performs a fast, lightweight data pull for every configured MSSP tenant
and returns a single Markdown table suitable for a NOC wallboard or
morning health check. No full snapshot extraction is run — only targeted
REST calls for rule counts, remote networks, IKE tunnels, and licences.

Columns:
    Tenant        — tenant label from settings.toml
    Rules         — security rule count (pre-rulebase, Shared folder)
    RNs           — remote network (branch) count
    Tunnels       — IKE gateway count
    PAB           — Prisma Access Browser: enrolled users/devices and the
                    share of devices passing all posture checks (screen
                    lock + disk encryption + firewall); — if unprovisioned
    Nearest Expiry — soonest licence expiry date (see include_expired)
    Days          — days until that expiry
    Lic           — licence RAG status
    Errors        — API call failures during this poll
    RAG           — overall tenant health (🔴 / 🟡 / 🟢)

Args:
    include_expired: When False (default), already-expired SKUs are
        excluded from the nearest-expiry calculation so the RAG reflects
        operational licence health — i.e. the soonest renewal among
        *active* licences — rather than being dragged permanently
        negative by a long-dead trial/legacy SKU (e.g. an old
        logging_service Production License). A tenant whose licences are
        *all* expired still falls back to its worst expired SKU and flags
        red. Set True to compute the nearest expiry across every SKU.

Returns:
    Markdown table with one row per tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `include_expired` | `bool` | `False` |

### `scm_spn_bandwidth`

SPN bandwidth allocation, live throughput, and oversubscription risk.

```
Fetches configured bandwidth allocations (Mbps) per SPN region and
cross-references them against the remote networks (branches) connected to
each SPN.  Also queries the Prisma Access Insights API for live per-SPN
throughput (Mbps in/out, 5-minute rolling average) and shows utilisation
percentage against the configured allocation.

Risk thresholds (configurable):
    HIGH    — per-branch share < risk_threshold_low Mbps (default 5)
    MEDIUM  — per-branch share < risk_threshold_med Mbps (default 10)
    LOW     — per-branch share >= risk_threshold_med Mbps
    UNALLOCATED — SPN has branches but no bandwidth-allocation entry

Live throughput is fetched from the Insights v3.0 API using the same
OAuth session as the SCM config API.  If the tenant's token scope does not
include Insights access the throughput columns are omitted and the report
falls back to allocation-only mode automatically.

Args:
    tenant_id: SCM tenant ID (MSSP mode). Leave empty for the active tenant.
    all_tenants: If True, report across all configured MSSP tenants.
    risk_threshold_low: Per-branch Mbps below which risk is HIGH (default 5).
    risk_threshold_med: Per-branch Mbps below which risk is MEDIUM (default 10).

Returns:
    Markdown report: per-SPN allocation + live throughput table, branch
    roster, QoS config, aggregate totals, and oversubscription risk summary.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `all_tenants` | `bool` | `False` |
| `risk_threshold_low` | `int` | `5` |
| `risk_threshold_med` | `int` | `10` |

### `scm_gp_session_summary`

Live GlobalProtect and Prisma Access Agent session summary.

```
Queries the Prisma Access Insights API for current connected mobile-user
session counts and breaks them down by:
  - Country of origin (client-side GeoIP)
  - Compute node / PA edge location
  - Client type: GlobalProtect vs Prisma Access Agent
  - GP client version distribution

Compares the live connected count against the licensed MU seat count and
shows utilisation as a percentage.

**Privacy:** Only aggregate counts are returned — no usernames, IP addresses,
or device identifiers appear in the output.

Args:
    tenant_id: SCM tenant ID (MSSP mode). Leave empty for the active session.

Returns:
    Markdown report: headline utilisation, country table, compute-node table,
    agent-type and GP-version breakdown.  Sections that return no data from
    the Insights API are omitted rather than shown as empty tables.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

### `scm_check_updates`

Check for SDK, dependency, and pan.dev API documentation updates.

```
Queries PyPI for the latest published versions of all Python packages
used by this server and compares them against installed versions.
Also checks GitHub for the latest pan-scm-sdk release notes and
recent commits to the PAN SASE OpenAPI specs on pan.dev.

No credentials required — reads PyPI and public GitHub APIs only.
Uses `urllib.request` from the standard library; no new dependencies.

Returns:
    Markdown report with:
      • Package version table (installed vs latest, update flag)
      • pan-scm-sdk latest release notes excerpt
      • Recent pan.dev SASE OpenAPI spec commit log
```

### `scm_device_summary`

Device inventory health summary — count by model, connection, HA state.

```
Queries ``GET /config/setup/v1/devices`` and aggregates:
  - Total device count
  - Connected vs offline split
  - HA state breakdown (active / passive / standalone / unknown)
  - Count per model

Args:
    folder: SCM folder to query (default: "ngfw-shared").
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    Markdown report with summary table and per-model breakdown.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'ngfw-shared'` |
| `tenant_id` | `str` | `''` |

### `scm_user_count`

Live connected user count across Prisma Access and NGFW.

```
Queries the Prisma Access Insights v3.0 API for current connected
user counts, split between GlobalProtect mobile users (Prisma Access)
and Prisma Access Agent users (NGFW-managed endpoints).

Also pulls the licensed Mobile User seat count for utilisation %.

Args:
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    Markdown report: headline total, GP vs Agent split, licensed
    capacity and utilisation percentage.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |

---

## Posture Management

_SCM Posture Management and Incidents APIs._

### `scm_incident_search`

Search SCM security incidents via the Incidents API (March 2026).

```
Queries `POST /incidents/v1/search` for security incidents raised by
Strata Cloud Manager across Prisma Access, NGFW, and SCM platform events.
Returns a prioritised incident table sorted by severity and raise time.

Incident types include: dataplane upgrades, tunnel failures, certificate
expiry, licence issues, threat events, and platform health events.

Args:
    severity: Comma-separated filter — Critical,High,Medium,Low
              (e.g. "Critical,High"). Empty = all severities.
    status: Comma-separated filter — Open,Closed,Acknowledged.
            Empty = all statuses.
    product: Filter by product — "Prisma Access", "SCM", etc.
             Empty = all products.
    acknowledged: Filter by acknowledgement — "true", "false", or "".
    days: Look-back window in days (default 30, max 180).
    limit: Max incidents to return per tenant (default 100).
    all_tenants: Sweep all configured MSSP tenants.
    tenant_id: Specific tenant ID. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `severity` | `str` | `''` |
| `status` | `str` | `''` |
| `product` | `str` | `''` |
| `acknowledged` | `str` | `''` |
| `days` | `int` | `30` |
| `limit` | `int` | `100` |
| `all_tenants` | `bool` | `False` |
| `tenant_id` | `str` | `''` |

### `scm_incident_summary`

Cross-tenant SCM incident NOC dashboard.

```
Fetches incidents from all (or a single) MSSP tenant and produces
a traffic-light summary table: count of Critical/High/Medium/Low/Total
incidents per tenant alongside the most recent open critical incident title.

Ideal for morning NOC briefings and MSSP SLA reporting.

Args:
    days: Look-back window in days (default 7).
    all_tenants: Sweep all configured tenants (default True).
    tenant_id: Specific tenant ID when all_tenants=False.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `days` | `int` | `7` |
| `all_tenants` | `bool` | `True` |
| `tenant_id` | `str` | `''` |

### `scm_posture_report`

Retrieve SCM Posture Management best-practice report findings.

```
Queries the Posture Management API (`/posture/v1/reports`) introduced
March 2026. Returns security posture findings across SCM-managed devices
including policy gaps, configuration drift, and compliance deviations.

**Note:** Requires the Posture Management add-on licence for your SCM
subscription. Contact your PAN account team or MSSP admin to enable.
The Posture Management API currently covers the Best Practice Report
module; Compliance, Policy Optimizer, Policy Analyzer, and Config Cleanup
modules are in development.

Args:
    folder: SCM folder scope (default "Shared").
    tenant_id: SCM tenant ID. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `'Shared'` |
| `tenant_id` | `str` | `''` |

### `scm_saas_posture`

SaaS Security Posture (SSPM): app posture, findings, and IdPs.

```
Queries the SSPM API for onboarded SaaS applications with their
per-app misconfiguration findings (severity-ranked), the supported
app catalog, and Identity-SSPM IdP/NHI posture, and renders a
markdown summary. Unlicensed / unprovisioned tenants are reported
clearly rather than erroring.

Manual export/import:
- `save_to`: also write the raw posture snapshot (apps + findings +
  IdPs + catalog) to a JSON file for archiving, diffing between
  runs, or sharing.
- `load_from`: render a previously exported JSON file instead of
  calling the API — offline review of an archived snapshot.

Args:
    tenant_id: SCM tenant ID (MSSP mode). Ignored with load_from.
    include_catalog: Also list the supported-app catalog by vertical.
    save_to: Path to export the snapshot JSON to.
    load_from: Path of a previous export to render instead of live data.

Returns:
    Markdown posture summary (plus export confirmation when saved).
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `include_catalog` | `bool` | `False` |
| `save_to` | `str` | `''` |
| `load_from` | `str` | `''` |

---

## Advanced DNS Security & NGFW Operations

_Advanced DNS Security Resolver (ADNSR) and NGFW Operations APIs._

### `scm_adnsr_list`

List Advanced DNS Security Resolver (ADNSR) resources.

```
Queries the ADNSR API (`/adns-resolver/v1/`) introduced May 2026.
ADNSR provides enterprise DNS security with custom resolvers, internal
domain bypass, EDL-based domain blocking, sinkholing, and CA certificate
management — all configurable per Prisma Access tenant.

**Requires Advanced DNS Security Resolver licence** (separate add-on).

Resources available:
- `profiles` — DNS security profiles (default)
- `internal-domains` — internal domain bypass rules
- `connection-sources` — resolver source IP/interface config
- `custom-fqdns` — custom FQDN override entries
- `edl-definitions` — external dynamic list DNS definitions
- `misconfigured-domains` — detected misconfigured domain records
- `resolver-info` — resolver health and connectivity status
- `ca-certs` — trusted CA certificates for DNS-over-TLS

Args:
    resource: Resource type to list (see above, default "profiles").
    folder: SCM folder scope (default "Shared").
    tenant_id: SCM tenant ID. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `resource` | `str` | `'profiles'` |
| `folder` | `str` | `'Shared'` |
| `tenant_id` | `str` | `''` |

### `scm_adnsr_profile_create`

Create an Advanced DNS Security Resolver profile.

```
Creates a new ADNSR DNS security profile via `POST /adns-resolver/v1/profiles`.
Profiles control how DNS queries are inspected, blocked, or sinkhol'd for
malicious domains. Use `scm_adnsr_list` to check existing profiles first.

**Requires Advanced DNS Security Resolver licence.**

Args:
    name: Profile name (must be unique within the folder).
    folder: SCM folder scope (default "Shared").
    action: Default action for threat domains — "sinkhole" (default),
            "block", or "allow".
    log_queries: Enable DNS query logging (default True).
    tenant_id: SCM tenant ID. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `name` | `str` | `—` |
| `folder` | `str` | `'Shared'` |
| `action` | `str` | `'sinkhole'` |
| `log_queries` | `bool` | `True` |
| `tenant_id` | `str` | `''` |

### `scm_ngfw_local_config_list`

List local configuration versions pushed to a specific SCM-managed NGFW.

```
Uses the NGFW Operations API (`GET /sse/config/v1/local-config/versions`)
introduced May 2026. Returns the history of configuration versions that
SCM has pushed to the device, including timestamps and version identifiers.

Use `scm_ngfw_device_list` to find valid device serial numbers first.

**Requires NGFW Operations entitlement** on the TSG.

Args:
    serial: Device serial number (e.g. "007351000123456").
    tenant_id: SCM tenant ID. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `serial` | `str` | `—` |
| `tenant_id` | `str` | `''` |

### `scm_ngfw_local_config_get`

Fetch the XML configuration file for a specific NGFW local config version.

```
Uses the NGFW Operations API to retrieve the actual PAN-OS XML config
that was pushed to the device. The returned XML can be fed directly into
`scm_aiops_bpa` for device-level Best Practice Assessment without manual
config export.

Workflow: `scm_ngfw_device_list` → `scm_ngfw_local_config_list` →
`scm_ngfw_local_config_get` → `scm_aiops_bpa(config_xml=...)`

**Requires NGFW Operations entitlement** on the TSG.

Args:
    serial: Device serial number.
    version: Config version identifier from `scm_ngfw_local_config_list`,
             or "running" for the currently active config (default).
    tenant_id: SCM tenant ID. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `serial` | `str` | `—` |
| `version` | `str` | `'running'` |
| `tenant_id` | `str` | `''` |

### `scm_ngfw_wan_ip_summary`

Report configured WAN/internet-facing interface IP addresses for NGFW devices.

```
For each SCM-managed NGFW device (or just `serial` if given), fetches its
running-config via the NGFW Operations API and parses physical/aggregate
interfaces (ethernetX/Y, aeN) that have Layer 3 addressing, along with
their assigned security zone.

With enrich=true, each public interface IP is additionally looked up
against an external IP-intelligence provider (ISP, organisation, ASN,
reverse DNS, IP geolocation). Note this sends the tenant's public IPs
to a third-party service (`ip_enrichment_provider` in settings, default
ip-api.com) — hence opt-in, never on by default.

Use this to populate a WAN IP inventory table for AS-BUILT documentation.
Note: this reflects **configuration**, not live operational state — a
DHCP-configured interface is reported with addressing="dhcp" but no IP,
since (unlike Prisma SD-WAN) there is no live-lease-status endpoint for
NGFW interfaces.

**Requires NGFW Operations entitlement** on the TSG.

Args:
    tenant_id: SCM tenant ID. Defaults to active tenant.
    serial: Optional — limit to a single device serial number.
    enrich: Look up ISP/ASN/rDNS/geo for each public interface IP.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `serial` | `str` | `''` |
| `enrich` | `bool` | `False` |

---

## AIOps

_PAN AIOps BPA integration._

### `scm_aiops_bpa`

Submit a PAN-OS device config XML to the PAN AIOps BPA API for analysis.

```
Runs PAN's first-party Best Practice Assessment engine against a live
PAN-OS or Panorama configuration, complementing the 39 SCM-based BPA
checks with PAN's own device-level analysis. Reports include per-category
scores and a prioritised list of failing checks with recommendations.

**IMPORTANT — requester identity:** The AIOps BPA API (`api.stratacloud
.paloaltonetworks.com/aiops/bpa/v1`) validates `requester_email` against
registered PANW Customer Support Portal (CSP) accounts linked to the TSG.
Use the email address you use to log in to the PANW CSP / AIOps portal.
Contact bpa@paloaltonetworks.com to enable BPA API access for your account.

**How to obtain the config XML:**
- PAN-OS CLI: `show config running | display xml` (copy full output)
- Panorama: Device tab → select device → Export Config (XML)
- SCM NGFW device: Admin UI → Devices → export running config

**Workflow:** POST `/requests` with device metadata → signed S3 upload URL
→ PUT config XML → poll `/jobs/{id}` → GET download URL → fetch report.

Args:
    config_xml: PAN-OS XML configuration string (full running config).
    requester_email: Email of a registered PANW CSP user with TSG access.
    requester_name: Display name for the requester (defaults to email prefix).
    device_serial: Device serial number (e.g. "007351000123456"). Use
        "UNKNOWN" if not available.
    device_family: Device family (e.g. "PA-VM", "PA-5200", "PA-3400").
    device_model: Device model (e.g. "PA-VM", "PA-5220", "PA-3420").
    device_version: PAN-OS version string (e.g. "10.2.9", "11.1.3").
    device_name: Optional label for the report header (e.g. "FW-NYC-01").
    timeout: Max seconds to wait for the BPA job to complete (default 120).
    tenant_id: SCM tenant ID for authentication. Defaults to active tenant.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `config_xml` | `str` | `—` |
| `requester_email` | `str` | `—` |
| `requester_name` | `str` | `''` |
| `device_serial` | `str` | `'UNKNOWN'` |
| `device_family` | `str` | `'PA-VM'` |
| `device_model` | `str` | `'PA-VM'` |
| `device_version` | `str` | `'10.2.0'` |
| `device_name` | `str` | `''` |
| `timeout` | `int` | `120` |
| `tenant_id` | `str` | `''` |

---

## AI Compliance Advisor

_AI-assisted compliance analysis (Anthropic API)._

### `scm_ai_compliance_advisor`

AI-powered compliance advisor: run NCSC/NIST gap checks then generate a remediation playbook and executive summary using Claude.

```
Combines the gap detection from scm_ncsc_gap / scm_nist_gap with an
AI layer that interprets findings in plain English and maps each gap
to concrete SCM remediation steps and MCP tool commands.

Output contains two sections:
  1. EXECUTIVE SUMMARY  — ≤150 words, risk-focused, suitable for reports
  2. REMEDIATION PLAYBOOK — one entry per gap (critical → info), with
     exact fix steps and estimated effort per item

Requirements:
  - ANTHROPIC_API_KEY environment variable (or SCM_MCP_ANTHROPIC_API_KEY)
  - pip/uv install anthropic>=0.40.0

Args:
    folder: SCM folder to inspect (e.g. "Shared" or a tenant folder).
    framework: "ncsc", "nist", or "both" (default: "both").
    position: Security rule position — "pre", "post", or "both".
    tenant_label: Human-readable tenant name shown in the report header.
    model: Override the Claude model (default: from settings / claude-sonnet-4-6).
```

| Parameter | Type | Default |
|-----------|------|---------|
| `folder` | `str` | `—` |
| `framework` | `str` | `'both'` |
| `position` | `str` | `'pre'` |
| `tenant_label` | `str` | `''` |
| `model` | `str` | `''` |

---

## Service Provider Interconnect

_SP backbone attach to Prisma Access: interconnects, physical connections, regions, settings, IP-pool usage (multitenant MSP API)._

### `scm_spi_status`

Service Provider Interconnect (SPI) inventory and status.

```
SPI attaches a service-provider backbone directly to Prisma Access
(native-IP on-ramp, no IPsec) and steers tenant egress through the SP
network. This tool reads the multitenant SPI API — the service account
needs an MSP role; a 403 means the account or TSG is not SPI-enrolled.

Args:
    view: What to show —
        "summary"              interconnect roll-up (default)
        "interconnects"        all interconnects
        "physical-connections" physical connections across interconnects
        "regions"              SPI-capable regions
        "region-connections"   physical connections per region
        "settings"             SPI tenant settings
        "ip-pool-usage"        monitor: IP pool consumption
    tenant_id: SCM tenant ID (MSSP mode).
    interconnect_id: Filter ip-pool-usage to one interconnect.
    cloud_provider: Filter regions view by cloud provider.
    usage: Summary view usage filter.
    include_default_interconnect: interconnects view — include default.
    include_tenants_associated: interconnects view — include tenant associations.

Returns:
    Markdown with a JSON payload, or an actionable message on 4xx.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `view` | `str` | `'summary'` |
| `tenant_id` | `str` | `''` |
| `interconnect_id` | `str` | `''` |
| `cloud_provider` | `str` | `''` |
| `usage` | `str` | `''` |
| `include_default_interconnect` | `bool` | `False` |
| `include_tenants_associated` | `bool` | `False` |

---

## Prisma Access Browser for MSP

_Region-level PAB summaries and per-TSG security-event reports (multitenant MSP API)._

### `scm_pab_msp_summary`

Prisma Access Browser MSP summary — users, tenants, or CIE.

```
Region-level roll-ups from the PAB for MSP API (multitenant; the
service account needs an MSP role and a PAB entitlement — a 403
message explains what is missing).

Args:
    scope: "tenants" (per-tenant summary, default), "users"
           (configured-user counts), or "cie" (Cloud Identity
           Engine summary).
    region: PAB SLS region identifier — one of: americas, europe,
            jp, uk, in, sg, ca, id, au, de (default "europe").
    tenant_id: SCM tenant ID (MSSP mode).

Returns:
    Markdown with a JSON payload, or an actionable message on 4xx.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `scope` | `str` | `'tenants'` |
| `region` | `str` | `'europe'` |
| `tenant_id` | `str` | `''` |

### `scm_pab_msp_report`

Prisma Access Browser MSP security-event report for one tenant.

```
Pulls a PAB security report for a TSG: blocked malware, blocked or
malicious websites, blocked extensions, and category breakdowns.
Useful evidence for browser-security controls in CE/NCSC reporting.

Args:
    report: One of: count, extension_blocked, extension_category,
            malicious_website, malware_blocked, malware_website,
            website_blocked, website_category.
    tsg_id: Tenant Service Group to report on. Defaults to tenant_id.
    tenant_id: SCM tenant ID used for auth (MSSP mode).

Returns:
    Markdown with a JSON payload, or an actionable message on 4xx.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `report` | `str` | `'count'` |
| `tsg_id` | `str` | `''` |
| `tenant_id` | `str` | `''` |

---

## Utility

_Hot-reload and restart of the running MCP server._

### `scm_reload`

Hot-reload scm_mcp_mssp source modules without restarting the MCP server.

```
Reloads all scm_mcp_mssp submodules in dependency order, patches
cross-module references, then re-registers all tools so edits to a
tool's own body take effect immediately.

Args:
    modules: Optional list of short module names to reload (e.g.
             ["asbuilt_report", "extractor"]).  If omitted, all modules
             in the standard reload list are refreshed.

Returns:
    Summary of reloaded modules, patched references, and any errors.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `modules` | `list[str] \| None` | `None` |

### `scm_restart`

Restart the MCP server process.

```
Schedules a clean exit after returning this response.  Claude Desktop
and most MCP supervisors detect the exit and automatically reconnect /
restart the server.  Use this when a hot-reload (`scm_reload`) is not
enough — e.g. after adding a new dependency, changing `server.py`,
editing config files, or installing an SDK update.

For the HTTP transport (`scm-mcp-http`) the process must be managed by
a supervisor (systemd, Docker restart policy) for automatic restart to
occur; otherwise it simply exits and must be restarted manually.

Args:
    delay_seconds: Seconds to wait before sending SIGTERM (default 3,
                   minimum 1).  The delay lets this response be
                   delivered before the process terminates.

Returns:
    Confirmation that restart has been scheduled.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `delay_seconds` | `int` | `3` |

---

## Pab

_Prisma Access Browser — tenant-level management/inventory tools._

### `scm_pab_inventory`

Prisma Access Browser enrolled users, devices, and posture.

```
Views:
- summary: counts — users by status, devices by OS, and endpoint
  posture compliance (screen lock / disk encryption / firewall
  enabled) across the device fleet.
- users: enrolled browser users (email, status, provider,
  first/last seen, groups).
- devices: device inventory with per-device posture status,
  OS/model/serial, and last seen.
- user_groups / device_groups: group definitions (device groups
  carry the posture-policy platform).

Unprovisioned tenants report clearly (users/devices come back
empty while config endpoints return "tenant not found").

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    view: summary | users | devices | user_groups | device_groups.
    limit: Max records per list view (default 50, cursor-paginated).
    os_type: devices view — filter by OS type (e.g. macOS, Windows).
    user_status: users view — filter by status (e.g. active).

Returns:
    JSON with the requested view plus any endpoint warnings.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `view` | `str` | `'summary'` |
| `limit` | `int` | `50` |
| `os_type` | `str` | `''` |
| `user_status` | `str` | `''` |

### `scm_pab_apps`

Prisma Access Browser application catalog and app groups.

```
Views:
- apps: configured applications (name, type, category, URLs) with
  optional type/name filters.
- categories: the list of application categories.
- app_groups: application group definitions.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    view: apps | categories | app_groups.
    app_type: apps view — filter by application type.
    name: apps view — search by name.
    limit: Max records (default 50).

Returns:
    JSON with the requested view.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `view` | `str` | `'apps'` |
| `app_type` | `str` | `''` |
| `name` | `str` | `''` |
| `limit` | `int` | `50` |

### `scm_pab_user_requests`

Prisma Access Browser user access requests (helpdesk queue).

```
Lists end-user requests raised from the browser (e.g. access to a
blocked site or app) with their status — the queue an admin
approves or denies in the PAB console.

Args:
    tenant_id: SCM tenant ID (MSSP mode).
    status: Filter by request status.
    request_type: Filter by request type.
    limit: Max records (default 50).

Returns:
    JSON array of user requests.
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tenant_id` | `str` | `''` |
| `status` | `str` | `''` |
| `request_type` | `str` | `''` |
| `limit` | `int` | `50` |
