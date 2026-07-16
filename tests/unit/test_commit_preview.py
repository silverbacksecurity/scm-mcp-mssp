"""Unit tests for the commit blast-radius gate (audit/commit_preview.py).

Pins down the shadow-detection heuristic (any-coverage, literal supersets,
focus filtering, disabled rules), the BPA introduced/resolved delta, verdict
triage, and the rendered report's load-bearing content.
"""

from __future__ import annotations

from scm_mcp_mssp.audit.asbuilt_verify import diff_snapshots
from scm_mcp_mssp.audit.commit_preview import (
    bpa_delta,
    find_shadowed_rules,
    preview_verdict,
    render_commit_preview,
)
from scm_mcp_mssp.audit.models import AuditSnapshot, Finding, Severity, Status


def _rule(name: str, **over: object) -> dict:
    rule = {
        "name": name,
        "action": "allow",
        "from_": ["any"],
        "to_": ["any"],
        "source": ["any"],
        "destination": ["any"],
        "application": ["any"],
        "service": ["any"],
        "disabled": False,
    }
    rule.update(over)
    return rule


class TestFindShadowedRules:
    def test_any_rule_shadows_everything_below(self) -> None:
        rules = [_rule("allow-all"), _rule("block-web", action="deny")]
        (s,) = find_shadowed_rules(rules)
        assert s["shadowed"] == "block-web" and s["by"] == "allow-all"

    def test_literal_superset_shadows(self) -> None:
        rules = [
            _rule("broad", source=["10.0.0.0/8"], application=["web-browsing", "ssl"]),
            _rule("narrow", source=["10.0.0.0/8"], application=["ssl"]),
        ]
        (s,) = find_shadowed_rules(rules)
        assert s["shadowed"] == "narrow"

    def test_narrower_earlier_rule_does_not_shadow(self) -> None:
        rules = [
            _rule("narrow", source=["10.1.1.0/24"]),
            _rule("broad", source=["10.0.0.0/8"]),
        ]
        assert find_shadowed_rules(rules) == []

    def test_any_in_later_rule_is_not_covered_by_specific_earlier(self) -> None:
        rules = [_rule("specific", source=["10.1.1.1"]), _rule("catchall")]
        assert find_shadowed_rules(rules) == []

    def test_disabled_rules_are_ignored(self) -> None:
        rules = [_rule("allow-all", disabled=True), _rule("block-web", action="deny")]
        assert find_shadowed_rules(rules) == []

    def test_focus_names_filters_untouched_pairs(self) -> None:
        rules = [_rule("old-catchall"), _rule("old-below", action="deny")]
        # Pre-existing shadow, but neither rule is part of the pending change
        assert find_shadowed_rules(rules, focus_names={"new-rule"}) == []
        # Pending change includes the shadowed rule → reported
        assert len(find_shadowed_rules(rules, focus_names={"old-below"})) == 1


def _finding(check_id: str, status: Status, sev: Severity = Severity.HIGH) -> Finding:
    return Finding(
        check_id=check_id,
        title=f"title {check_id}",
        severity=sev,
        status=status,
        description="",
        remediation="",
    )


class TestBpaDelta:
    def test_introduced_and_resolved_split(self) -> None:
        ref = [_finding("A", Status.FAIL), _finding("B", Status.PASS)]
        cand = [_finding("A", Status.PASS), _finding("B", Status.FAIL)]
        introduced, resolved = bpa_delta(ref, cand)
        assert [f.check_id for f in introduced] == ["B"]
        assert [f.check_id for f in resolved] == ["A"]

    def test_unchanged_fails_are_neither(self) -> None:
        ref = [_finding("A", Status.FAIL)]
        cand = [_finding("A", Status.FAIL)]
        introduced, resolved = bpa_delta(ref, cand)
        assert introduced == [] and resolved == []

    def test_introduced_sorted_most_severe_first(self) -> None:
        cand = [
            _finding("low", Status.FAIL, Severity.LOW),
            _finding("crit", Status.FAIL, Severity.CRITICAL),
        ]
        introduced, _ = bpa_delta([], cand)
        assert [f.check_id for f in introduced] == ["crit", "low"]


def _diffs(base: AuditSnapshot, cand: AuditSnapshot):
    return [d for d in diff_snapshots(base, cand) if d.drifted]


def _snap(**fields: object) -> AuditSnapshot:
    snap = AuditSnapshot(folder="Prisma Access", tenant_id="t1")
    for name, value in fields.items():
        setattr(snap, name, value)
    return snap


class TestPreviewVerdict:
    def test_no_changes(self) -> None:
        assert preview_verdict([], [], []) == "NO CHANGES"

    def test_low_risk_for_object_plumbing_additions(self) -> None:
        diffs = _diffs(_snap(tags=[]), _snap(tags=[{"name": "new-tag"}]))
        assert preview_verdict(diffs, [], []) == "LOW RISK"

    def test_high_section_addition_is_review(self) -> None:
        diffs = _diffs(
            _snap(security_rules_pre=[]),
            _snap(security_rules_pre=[_rule("new-rule")]),
        )
        assert preview_verdict(diffs, [], []) == "REVIEW"

    def test_high_section_removal_is_high_risk(self) -> None:
        diffs = _diffs(
            _snap(security_rules_pre=[_rule("old-rule")]),
            _snap(security_rules_pre=[]),
        )
        assert preview_verdict(diffs, [], []) == "HIGH RISK"

    def test_shadowing_is_high_risk(self) -> None:
        diffs = _diffs(_snap(tags=[]), _snap(tags=[{"name": "t"}]))
        shadows = [{"shadowed": "b", "by": "a", "detail": "x"}]
        assert preview_verdict(diffs, shadows, []) == "HIGH RISK"

    def test_new_high_bpa_finding_is_high_risk(self) -> None:
        diffs = _diffs(_snap(tags=[]), _snap(tags=[{"name": "t"}]))
        introduced = [_finding("X", Status.FAIL, Severity.HIGH)]
        assert preview_verdict(diffs, [], introduced) == "HIGH RISK"


class TestRenderCommitPreview:
    def _render(self, diffs, shadows=(), introduced=(), resolved=()) -> str:
        return render_commit_preview(
            list(diffs),
            list(shadows),
            list(introduced),
            list(resolved),
            tenant_label="t1",
            folder="Prisma Access",
            baseline_saved_at="2026-07-14",
            generated_at="2026-07-15 09:00 UTC",
        )

    def test_no_op_report(self) -> None:
        report = self._render([])
        assert "NO PENDING CHANGES" in report
        assert "Next Step" not in report

    def test_high_risk_report_names_everything(self) -> None:
        diffs = _diffs(
            _snap(security_rules_pre=[_rule("keep"), _rule("dropped")]),
            _snap(security_rules_pre=[_rule("keep")]),
        )
        shadows = [{"shadowed": "b", "by": "a", "detail": "`a` covers `b`"}]
        introduced = [_finding("BPA-X", Status.FAIL)]
        report = self._render(diffs, shadows, introduced)
        assert "HIGH RISK" in report
        assert "`dropped`" in report
        assert "`a` covers `b`" in report
        assert "BPA-X" in report
        assert "scm_commit" in report and "update_baseline=True" in report

    def test_resolved_findings_shown_as_wins(self) -> None:
        diffs = _diffs(_snap(tags=[]), _snap(tags=[{"name": "t"}]))
        report = self._render(diffs, resolved=[_finding("BPA-FIXED", Status.FAIL)])
        assert "Resolved by This Change" in report and "BPA-FIXED" in report
