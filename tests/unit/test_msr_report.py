"""Tests for the MSR — Monthly Service Review pack generator.

Covers:
  - month_bounds parsing + previous-month default (incl. January rollover)
  - in_period boundary behaviour
  - SSR provenance-note parsing (all three note shapes, legacy prefixes)
  - compute_service_stats (MTTR from closed incidents, change failure rate,
    honest n/a when resolution timestamps are absent)
  - render_msr_report tier gating (bronze/silver/gold compliance depth)
  - renderer degradation notes (§8 coverage disclosure)
  - gather_msr_data period filtering + per-source degradation with a mock client
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from scm_mcp_mssp.audit.msr_report import (
    MsrData,
    compute_service_stats,
    in_period,
    month_bounds,
    parse_ssr_notes,
    render_msr_report,
)

# ---------------------------------------------------------------------------
# month_bounds / in_period
# ---------------------------------------------------------------------------


class TestMonthBounds:
    def test_explicit_month(self) -> None:
        start, end, label = month_bounds("2026-06")
        assert start == datetime(2026, 6, 1, tzinfo=UTC)
        assert end == datetime(2026, 7, 1, tzinfo=UTC)
        assert label == "2026-06"

    def test_december_rolls_into_next_year(self) -> None:
        start, end, _ = month_bounds("2025-12")
        assert end == datetime(2026, 1, 1, tzinfo=UTC)

    def test_default_is_previous_full_month(self) -> None:
        _, _, label = month_bounds(now=datetime(2026, 7, 17, tzinfo=UTC))
        assert label == "2026-06"

    def test_january_defaults_to_prior_december(self) -> None:
        start, _, label = month_bounds(now=datetime(2026, 1, 5, tzinfo=UTC))
        assert label == "2025-12"
        assert start.year == 2025

    @pytest.mark.parametrize("bad", ["2026", "06-2026", "2026-13", "2026-00", "banana"])
    def test_malformed_month_raises(self, bad: str) -> None:
        with pytest.raises(ValueError):
            month_bounds(bad)


class TestInPeriod:
    START, END, _ = month_bounds("2026-06")

    def test_inside(self) -> None:
        assert in_period("2026-06-15T12:00:00Z", self.START, self.END)

    def test_start_inclusive_end_exclusive(self) -> None:
        assert in_period("2026-06-01T00:00:00Z", self.START, self.END)
        assert not in_period("2026-07-01T00:00:00Z", self.START, self.END)

    def test_unparseable_is_excluded(self) -> None:
        assert not in_period("not a date", self.START, self.END)
        assert not in_period(None, self.START, self.END)


# ---------------------------------------------------------------------------
# SSR ledger parsing
# ---------------------------------------------------------------------------


class TestParseSsrNotes:
    def test_all_three_note_shapes(self) -> None:
        desc = (
            "Customer allow list | SSR add: example.com — INC-1 | "
            "SSR threat-exception remove: 55555 — CHG-2 | "
            "SSR ssl-decrypt add: gambling — INC-3"
        )
        entries = parse_ssr_notes(desc, "SSR-Obj")
        assert [e["kind"] for e in entries] == ["url-list", "threat-exception", "ssl-decrypt"]
        assert entries[0] == {
            "object": "SSR-Obj",
            "kind": "url-list",
            "action": "add",
            "target": "example.com",
            "ticket_ref": "INC-1",
        }
        assert entries[1]["action"] == "remove"
        assert entries[2]["ticket_ref"] == "INC-3"

    def test_non_ssr_description_yields_nothing(self) -> None:
        assert parse_ssr_notes("Managed by MSSP — change freeze Dec") == []

    def test_empty_and_none_safe(self) -> None:
        assert parse_ssr_notes("") == []
        assert parse_ssr_notes(None) == []  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Service stats
# ---------------------------------------------------------------------------


def _inc(
    sev: str, status: str, raised: str, resolved: str | None = None, ack: bool = False
) -> dict:
    d = {"severity": sev, "status": status, "raised_time": raised, "acknowledged": ack}
    if resolved:
        d["resolved_time"] = resolved
    return d


class TestServiceStats:
    def test_mttr_from_closed_incidents(self) -> None:
        stats = compute_service_stats(
            [
                _inc("High", "Closed", "2026-06-01T00:00:00Z", "2026-06-01T04:00:00Z"),
                _inc("Low", "Closed", "2026-06-02T00:00:00Z", "2026-06-02T02:00:00Z"),
            ],
            [],
        )
        assert stats["mttr_hours"] == 3.0
        assert stats["mttr_samples"] == 2
        assert stats["open_at_generation"] == 0

    def test_no_resolution_timestamps_is_none_not_zero(self) -> None:
        stats = compute_service_stats(
            [_inc("High", "Closed", "2026-06-01T00:00:00Z")],
            [],
        )
        assert stats["mttr_hours"] is None

    def test_open_and_ack_counting(self) -> None:
        stats = compute_service_stats(
            [
                _inc("Critical", "Open", "2026-06-01T00:00:00Z", ack=True),
                _inc("Medium", "Acknowledged", "2026-06-02T00:00:00Z"),
            ],
            [],
        )
        assert stats["open_at_generation"] == 2
        assert stats["ack_rate_pct"] == 50
        assert stats["severity_counts"] == {"critical": 1, "medium": 1}

    def test_change_failure_rate(self) -> None:
        jobs = [{"result": "OK"}, {"result": "OK"}, {"result": "FAIL"}, {"result": "PENDING"}]
        stats = compute_service_stats([], jobs)
        assert stats["change_total"] == 4
        assert stats["change_ok"] == 2
        assert stats["change_failed"] == 1
        assert stats["change_failure_pct"] == 25

    def test_empty_period_rates_are_none(self) -> None:
        stats = compute_service_stats([], [])
        assert stats["ack_rate_pct"] is None
        assert stats["change_failure_pct"] is None


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def _base_data(tier: str = "gold") -> MsrData:
    return MsrData(
        tenant_label="Test Customer",
        tenant_id="t-1",
        tier=tier,
        period_label="2026-06",
        compliance_summaries=[
            {
                "id": "fw-1",
                "category": "regulatory",
                "benchmark": True,
                "revision_summary": [{"name": "CE Plus", "overall_score": 82.0, "state": "active"}],
            }
        ],
        compliance_timeline=[
            {"date": "2026-06-01", "overall_score": 85.0},
            {"date": "2026-06-30", "overall_score": 82.0},
        ],
        compliance_framework_name="CE Plus",
    )


class TestRenderer:
    def test_bronze_gates_compliance(self) -> None:
        md = render_msr_report(_base_data(tier="bronze"))
        assert "included at Silver tier" in md
        assert "CE Plus" not in md

    def test_silver_gets_summary_not_trend(self) -> None:
        md = render_msr_report(_base_data(tier="silver"))
        assert "| CE Plus |" in md
        assert "30-day score trend" not in md

    def test_gold_gets_trend_annex(self) -> None:
        md = render_msr_report(_base_data(tier="gold"))
        assert "30-day score trend" in md
        assert "Compliance score declined" in md  # 85 → 82 in exec summary

    def test_quiet_month_has_green_summary(self) -> None:
        md = render_msr_report(MsrData(tenant_label="T", tier="bronze", period_label="2026-06"))
        assert "🟢 No critical incidents" in md

    def test_incident_and_change_sections_render(self) -> None:
        data = _base_data()
        data.incidents = [
            _inc("Critical", "Open", "2026-06-03T10:00:00Z") | {"title": "Tunnel down"}
        ]
        data.jobs = [
            {
                "type": "CommitAndPush",
                "result": "FAIL",
                "user": "ops@mssp",
                "description": "policy update",
                "start_ts": "2026-06-04 10:00:00",
            }
        ]
        md = render_msr_report(data)
        assert "Tunnel down" in md
        assert "🔴 **1 Critical/High incident(s)**" in md
        assert "CommitAndPush" in md
        assert "change failure rate" in md

    def test_licence_table_splits_expired_and_compresses_ancient(self) -> None:
        data = _base_data()
        data.licence_rows = [
            {"app": "pae", "license_type": "NFR-A", "exp": "2026-09-01", "days": 64},
            {"app": "pae", "license_type": "EVAL-B", "exp": "2026-05-14", "days": -65},
            {"app": "pae", "license_type": "EVAL-OLD", "exp": "2025-04-20", "days": -454},
        ]
        md = render_msr_report(data)
        assert "| 64 🟠 |" in md
        assert "expired 65d ago 🔴" in md
        assert "EVAL-OLD" not in md
        assert "1 SKU group(s) expired more than 90 days ago (omitted)." in md

    def test_unassessed_framework_score_is_not_a_percentage(self) -> None:
        data = _base_data(tier="silver")
        data.compliance_summaries = [
            {
                "id": "fw-x",
                "category": "PCF",
                "benchmark": False,
                "revision_summary": [
                    {"name": "PCF Base", "overall_score": -1, "state": "released"}
                ],
            }
        ]
        md = render_msr_report(data)
        assert "| not assessed |" in md
        assert "-1%" not in md

    def test_source_errors_disclosed(self) -> None:
        data = _base_data()
        data.errors["licences"] = "HTTP 403 from subscription API"
        data.errors["bandwidth"] = "skipped (include_insights=False)"
        md = render_msr_report(data)
        assert "⚠️ Licence data unavailable: HTTP 403" in md
        assert "⚠️ bandwidth — skipped" in md

    def test_ssr_ledger_renders_cumulative_note(self) -> None:
        data = _base_data()
        data.ssr_ledger = [
            {
                "object": "SSR-Allow-List",
                "kind": "url-list",
                "action": "add",
                "target": "example.com",
                "ticket_ref": "INC-9",
            }
        ]
        md = render_msr_report(data)
        assert "Service-request ledger" in md
        assert "| SSR-Allow-List | url-list | add | example.com | INC-9 |" in md
        assert "not" in md and "period-only activity" in md


# ---------------------------------------------------------------------------
# gather_msr_data with a mock client
# ---------------------------------------------------------------------------


def _mock_job(start_ts: str, result: str = "OK") -> MagicMock:
    j = MagicMock()
    j.id = "job-1"
    j.type_str = "Commit"
    j.result_str = result
    j.uname = "admin@mssp"
    j.description = "change"
    j.start_ts = start_ts
    j.end_ts = start_ts
    return j


class TestGather:
    def _client(self, incidents: list[dict], jobs: list[MagicMock]) -> MagicMock:
        client = MagicMock()
        resp = MagicMock()
        resp.json.return_value = {"data": incidents}
        resp.raise_for_status.return_value = None
        client.session.post.return_value = resp
        client.list_jobs.return_value = MagicMock(data=jobs)
        return client

    def test_period_filtering_and_degradation(self) -> None:
        from scm_mcp_mssp.tools.msr import gather_msr_data

        incidents = [
            {"severity": "High", "status": "Open", "raised_time": "2026-06-10T00:00:00Z"},
            {"severity": "Low", "status": "Open", "raised_time": "2026-05-10T00:00:00Z"},  # out
        ]
        jobs = [_mock_job("2026-06-05 10:00:00"), _mock_job("2026-07-05 10:00:00")]
        client = self._client(incidents, jobs)
        # Licence + insights + compliance calls fail → degradation, not raise
        with (
            patch(
                "scm_mcp_mssp.tools.msr.fetch_licenses", side_effect=RuntimeError("licence boom")
            ),
            patch("scm_mcp_mssp.tools.msr.extract_insights", side_effect=RuntimeError("ins boom")),
            patch("scm_mcp_mssp.tools.msr._compliance_get", side_effect=RuntimeError("comp boom")),
            patch(
                "scm_mcp_mssp.tools.msr._resolve_tenant_meta",
                return_value=("T", "t-1", "gold", "uk"),
            ),
            patch("scm_mcp_mssp.tools.msr._get_ssr_config", return_value={}),
        ):
            data = gather_msr_data(client, tenant_id="t-1", month="2026-06")

        assert len(data.incidents) == 1
        assert data.incidents[0]["severity"] == "High"
        assert len(data.jobs) == 1
        assert data.errors.keys() >= {"licences", "bandwidth", "compliance"}
        # Degraded pack still renders end-to-end
        md = render_msr_report(data)
        assert "Monthly Service Review — T" in md
        assert "licence boom" in md

    def test_bronze_skips_compliance_entirely(self) -> None:
        from scm_mcp_mssp.tools.msr import gather_msr_data

        client = self._client([], [])
        with (
            patch("scm_mcp_mssp.tools.msr.fetch_licenses", return_value=[]),
            patch("scm_mcp_mssp.tools.msr._compliance_get") as comp,
            patch(
                "scm_mcp_mssp.tools.msr._resolve_tenant_meta",
                return_value=("T", "t-1", "bronze", "eu"),
            ),
            patch("scm_mcp_mssp.tools.msr._get_ssr_config", return_value={}),
        ):
            data = gather_msr_data(client, month="2026-06", include_insights=False)
        comp.assert_not_called()
        assert "compliance" not in data.errors

    def test_ssr_ledger_gathered_from_object_descriptions(self) -> None:
        from scm_mcp_mssp.tools.msr import gather_msr_data

        client = self._client([], [])
        obj = MagicMock()
        obj.model_dump.return_value = {
            "description": "SSR add: example.com — INC-1 | SSR add: foo.example — INC-2"
        }
        client.url_category.fetch.return_value = obj
        with (
            patch("scm_mcp_mssp.tools.msr.fetch_licenses", return_value=[]),
            patch(
                "scm_mcp_mssp.tools.msr._resolve_tenant_meta",
                return_value=("T", "t-1", "bronze", "eu"),
            ),
            patch(
                "scm_mcp_mssp.tools.msr._get_ssr_config",
                return_value={"url_allow_list": "SSR-Allow"},
            ),
            patch("scm_mcp_mssp.tools.msr._resolve_default_folder", return_value="Shared"),
        ):
            data = gather_msr_data(client, month="2026-06", include_insights=False)
        assert len(data.ssr_ledger) == 2
        assert data.ssr_ledger[0]["object"] == "SSR-Allow"
        assert data.ssr_ledger[1]["ticket_ref"] == "INC-2"
