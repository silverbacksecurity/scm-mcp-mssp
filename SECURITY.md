# Security Policy

## Supported versions

Only the latest release on `master` receives security fixes.

| Version | Supported |
|---------|-----------|
| latest  | ✅ |
| older   | ❌ |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing **silverbacksec@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix

You will receive an acknowledgement within 48 hours and a resolution timeline within 7 days.

## Scope

Issues in scope:
- Credential leakage (client secrets, tenant IDs appearing in logs or responses)
- Authentication bypass in the HTTP/SSE transport
- Injection vulnerabilities in MCP tool inputs passed to the SCM API
- Privilege escalation across MSSP tenants

Out of scope:
- Vulnerabilities in upstream dependencies (report to the relevant project)
- Issues requiring physical access to the host running the server
- Denial-of-service via SCM API rate limiting

## Security hardening notes

- `.secrets.toml` and `.env` are git-ignored — never commit credentials
- `client_secret` is stored as `SecretStr` and never appears in logs or `repr()`
- The HTTP/SSE transport requires API key or Entra ID authentication
- `gitleaks` and `bandit` run on every push via `security-scan.yml`
