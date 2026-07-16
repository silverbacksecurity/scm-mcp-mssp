"""
Pre-commit blast-radius analysis for the commit gate (scm_commit_preview).

Answers "what happens if I commit right now?" before scm_commit is issued:

  1. Pending changes — the candidate config (a fresh extraction reads
     candidate state) diffed against the drift baseline (last known-good),
     section by section, using the same diff engine as the drift sentinel.
  2. Rule shadowing — new/changed security rules that can never match
     because an earlier rule already covers their traffic, or that
     themselves shadow existing rules below them.
  3. BPA delta — best-practice findings the pending change introduces or
     resolves, by running the check engine against both states.

The verdict triages the lot into 🔴 HIGH RISK / 🟡 REVIEW / 🟢 LOW RISK with
every claim citing the object or check that produced it.

Pure functions only — no SCM client or MCP imports.
"""

from __future__ import annotations

from typing import Any

from .asbuilt_verify import SectionDiff, _name_list
from .drift_baseline import drift_severity
from .models import Finding, Status

# Rule match dimensions checked for shadowing. SDK model_dump() emits
# from_/to_ (Pydantic alias), raw REST emits from/to — accept either.
_MATCH_FIELDS = [
    ("from_", "from"),
    ("to_", "to"),
    ("source", "source"),
    ("destination", "destination"),
    ("application", "application"),
    ("service", "service"),
]


def _vals(rule: dict[str, Any], keys: tuple[str, str]) -> list[str]:
    raw = rule.get(keys[0]) or rule.get(keys[1]) or ["any"]
    return [str(v) for v in raw] if isinstance(raw, list) else [str(raw)]


def _covers(a: list[str], b: list[str]) -> bool:
    """True when rule-field values *a* cover every value in *b*."""
    if "any" in a:
        return True
    if "any" in b:
        return False
    return set(b) <= set(a)


def find_shadowed_rules(
    rules: list[dict[str, Any]],
    focus_names: set[str] | None = None,
) -> list[dict[str, str]]:
    """Detect rules that an earlier rule fully covers (classic shadow).

    Rule A shadows rule B when A precedes B and A's from/to/source/
    destination/application/service each cover B's — B can then never match.
    Membership overlap (address groups, EDLs, regions) isn't resolved, so
    this is a conservative literal-value check: it can miss shadows, but
    what it flags is real at the object level. One ordering caveat: the
    extracted rulebase merges rules from several folders, which approximates
    but may not equal SCM's true evaluation order — treat a flagged shadow
    as "verify the rule positions", not as proof.

    focus_names limits findings to pairs where the shadowing or shadowed
    rule is in the set (the pending change), keeping pre-existing shadow
    noise out of a commit preview. None means report everything.
    """
    active = [r for r in rules if not r.get("disabled")]
    findings: list[dict[str, str]] = []
    for i, earlier in enumerate(active):
        for later in active[i + 1 :]:
            e_name = str(earlier.get("name", "?"))
            l_name = str(later.get("name", "?"))
            if focus_names is not None and not ({e_name, l_name} & focus_names):
                continue
            if all(_covers(_vals(earlier, f), _vals(later, f)) for f in _MATCH_FIELDS):
                findings.append(
                    {
                        "shadowed": l_name,
                        "by": e_name,
                        "detail": (
                            f"`{e_name}` (action: {earlier.get('action', '?')}) precedes and "
                            f"fully covers `{l_name}` (action: {later.get('action', '?')}) — "
                            f"`{l_name}` can never match"
                        ),
                    }
                )
    return findings


def bpa_delta(
    reference: list[Finding], candidate: list[Finding]
) -> tuple[list[Finding], list[Finding]]:
    """(introduced, resolved) FAIL-status findings between the two states."""
    ref_fails = {f.check_id for f in reference if f.status == Status.FAIL}
    cand_fails = {f.check_id: f for f in candidate if f.status == Status.FAIL}
    introduced = [f for cid, f in cand_fails.items() if cid not in ref_fails]
    resolved = [f for f in reference if f.status == Status.FAIL and f.check_id not in cand_fails]
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    introduced.sort(key=lambda f: sev_order.get(str(f.severity), 9))
    resolved.sort(key=lambda f: sev_order.get(str(f.severity), 9))
    return introduced, resolved


def preview_verdict(
    diffs: list[SectionDiff],
    shadows: list[dict[str, str]],
    introduced: list[Finding],
) -> str:
    """HIGH RISK / REVIEW / LOW RISK / NO CHANGES."""
    if not diffs and not shadows and not introduced:
        return "NO CHANGES"
    new_high_bpa = any(str(f.severity) in ("critical", "high") for f in introduced)
    high_removals = any(drift_severity(d) == "HIGH" and (d.removed or d.changed) for d in diffs)
    if shadows or new_high_bpa or high_removals:
        return "HIGH RISK"
    if introduced or any(drift_severity(d) == "HIGH" for d in diffs):
        return "REVIEW"
    return "LOW RISK"


_VERDICT_LINE = {
    "NO CHANGES": "🟢 **NO PENDING CHANGES** — candidate matches the baseline; commit is a no-op",
    "LOW RISK": "🟢 **LOW RISK** — object plumbing only; no enforcement change detected",
    "REVIEW": "🟡 **REVIEW** — enforcement-relevant changes present; read the detail below",
    "HIGH RISK": "🔴 **HIGH RISK** — do not commit until every item below is explained",
}


def render_commit_preview(
    diffs: list[SectionDiff],
    shadows: list[dict[str, str]],
    introduced: list[Finding],
    resolved: list[Finding],
    tenant_label: str,
    folder: str,
    baseline_saved_at: str,
    generated_at: str,
) -> str:
    verdict = preview_verdict(diffs, shadows, introduced)
    lines = [
        "# Commit Preview — Blast Radius",
        "",
        f"**Tenant:** `{tenant_label}`  |  **Folder:** `{folder}`  |  "
        f"**Baseline:** {baseline_saved_at}  |  **Generated:** {generated_at}",
        "",
        _VERDICT_LINE[verdict],
        "",
    ]

    if diffs:
        lines += ["## Pending Changes vs Last Known-Good", ""]
        for d in diffs:
            sev = drift_severity(d)
            icon = {"HIGH": "🔴", "MEDIUM": "🟡"}.get(sev, "⚪")
            parts = []
            if d.added:
                parts.append(f"adds {_name_list(d.added, cap=10)}")
            if d.removed:
                parts.append(f"removes {_name_list(d.removed, cap=10)}")
            if d.changed:
                parts.append(f"modifies {_name_list(d.changed, cap=10)}")
            lines.append(f"- {icon} **[{sev}] {d.label}**: " + "; ".join(parts))
        lines.append("")

    if shadows:
        lines += ["## Rule Shadowing Introduced", ""]
        for s in shadows:
            lines.append(f"- 🔴 {s['detail']}")
        lines.append("")

    if introduced:
        lines += ["## Best-Practice Findings Introduced by This Change", ""]
        for f in introduced:
            objs = (
                f" — affects {_name_list(f.affected_objects, cap=5)}" if f.affected_objects else ""
            )
            lines.append(f"- 🔴 **[{str(f.severity).upper()}] {f.check_id}** {f.title}{objs}")
        lines.append("")

    if resolved:
        lines += ["## Findings Resolved by This Change", ""]
        for f in resolved:
            lines.append(f"- ✅ **{f.check_id}** {f.title}")
        lines.append("")

    if verdict == "NO CHANGES":
        return "\n".join(lines)

    lines += ["## Next Step", ""]
    if verdict == "HIGH RISK":
        lines.append("Resolve or explicitly accept each 🔴 item (change ticket reference), then:")
    else:
        lines.append("If the changes match the change ticket, proceed:")
    lines += [
        "",
        f'1. `scm_commit(folders=["{folder}"], description="<ticket ref>")`',
        f'2. `scm_drift_check(folder="{folder}", update_baseline=True)` — roll the '
        "baseline forward so the next preview diffs against this approved state.",
        "",
    ]
    return "\n".join(lines)
