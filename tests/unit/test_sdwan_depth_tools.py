"""Tests for the SD-WAN depth tools (events, audit, software, policy, link health).

No network — the prisma-sase client is replaced with a fake that serves
canned responses shaped like the live API (payload shapes were captured from
a live lab tenant).
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP

import scm_mcp_mssp.tools.sdwan as sdwan_tools


class FakeResp:
    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        status_code: int = 200,
        content: dict[str, Any] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self.sdk_status = status_code == 200
        if content is None:
            content = {"items": items or []}
        self.sdk_content = content if self.sdk_status else {}
        self._content = content
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._content


SITES = [
    {
        "id": "s1",
        "name": "Branch-1",
        "element_cluster_role": "SPOKE",
        "location": {"latitude": 51.5, "longitude": -0.12},
        "address": {"city": "London", "country": "United Kingdom"},
    },
    {"id": "s2", "name": "DC-1"},  # no coordinates — must be skipped by the map
]
ELEMENTS = [
    {
        "id": "e1",
        "name": "ion-1",
        "site_id": "s1",
        "model_name": "ion 3000",
        "serial_number": "30-1",
        "software_version": "6.5.2-b2",
        "connected": True,
    },
    {
        "id": "e2",
        "name": "ion-2",
        "site_id": "s2",
        "model_name": "ion 9000",
        "serial_number": "90-1",
        "software_version": "6.1.4-b2",
        "connected": False,
    },
]
EVENTS = [
    {
        "id": "ev1",
        "time": "2026-07-12T13:00:00Z",
        "code": "DEVICEHW_INTERFACE_DOWN",
        "type": "alarm",
        "severity": "major",
        "priority": "p2",
        "cleared": False,
        "acknowledged": False,
        "standing": True,
        "site_id": "s1",
        "element_id": "e1",
        "entity_ref": "tenants/t/elements/e1",
        "info": None,
        "correlation_id": "abc",
    },
    {
        "id": "ev2",
        "time": "2026-07-12T12:00:00Z",
        "code": "DEVICEHW_INTERFACE_DOWN",
        "type": "alarm",
        "severity": "major",
        "priority": "p2",
        "cleared": True,
        "acknowledged": False,
        "standing": False,
        "site_id": "s1",
        "element_id": "e1",
        "entity_ref": "tenants/t/elements/e1",
        "info": None,
        "correlation_id": "def",
    },
]
EVENTCODES = [
    {
        "code": "DEVICEHW_INTERFACE_DOWN",
        "display_name": "Interface Down",
        "category": "device",
        "type": "alarm",
    }
]
MACHINES = [
    {
        "id": "m1",
        "em_element_id": "e1",
        "sl_no": "30-1",
        "model_name": "ion 3000",
        "machine_state": "claimed",
        "image_version": "0.2",
        "connected": True,
    },
    {
        "id": "m2",
        "em_element_id": None,
        "sl_no": "30-2",
        "model_name": "ion 3000",
        "machine_state": "allocated",
        "image_version": "0.2",
        "connected": False,
    },
]
SOFTWARE_STATUS = [
    {
        "active_image_id": "img-old",
        "active_version": "6.5.2-b2",
        "upgrade_image_id": "img-new",
        "upgrade_state": "download_cancelled",
        "failure_info": "timed out",
        "_updated_on_utc": 2,
    },
    {"active_image_id": "img-1", "active_version": "6.5.1", "_updated_on_utc": 1},
]
NAT_SETS = [{"id": "ns1", "name": "NAT-Set", "description": None}]
NAT_RULES = [
    {
        "id": "nr1",
        "name": "Internet",
        "enabled": True,
        "protocol": 6,
        "actions": [{"type": "source_nat_dynamic"}],
        "source_zone_id": "z1",
        "destination_zone_id": None,
    }
]
ANYNETLINKS = [
    {
        "id": "p1",
        "name": None,
        "type": "AUTO-PUBLIC",
        "admin_up": True,
        "ep1_site_id": "s1",
        "ep2_site_id": "s2",
    },
    {
        "id": "p2",
        "name": None,
        "type": "AUTO-PUBLIC",
        "admin_up": False,
        "ep1_site_id": "s2",
        "ep2_site_id": "s3",
    },
]


def monitor_body(name: str, unit: str, values: list[float]) -> dict[str, Any]:
    return {
        "metrics": [
            {
                "series": [
                    {
                        "name": name,
                        "unit": unit,
                        "view": {"direction": "Ingress"},
                        "data": [
                            {
                                "statistics": "average",
                                "datapoints": [{"value": v} for v in values],
                            }
                        ],
                    }
                ]
            }
        ]
    }


def make_fake_sdk(*, auditlog_status: int = 200) -> Any:
    def monitor_metrics(payload: dict[str, Any]) -> FakeResp:
        name = payload["metrics"][0]["name"]
        unit = payload["metrics"][0]["unit"]
        return FakeResp(content=monitor_body(name, unit, [10.0, 20.0]))

    get = SimpleNamespace(
        sites=lambda site_id=None: FakeResp(SITES),
        elements=lambda element_id=None: FakeResp(ELEMENTS),
        wannetworks=lambda: FakeResp([{"id": "n1", "name": "BT-INET", "type": "publicwan"}]),
        waninterfaces=lambda site_id=None: FakeResp(
            [{"id": "swi1", "name": "Circuit-1", "network_id": "n1"}]
        ),
        eventcodes=lambda: FakeResp(EVENTCODES),
        machines=lambda: FakeResp(MACHINES),
        software_status=lambda eid: FakeResp(SOFTWARE_STATUS),
        natpolicysets=lambda: FakeResp(NAT_SETS),
        natpolicyrules=lambda sid: FakeResp(NAT_RULES),
        natpolicysetstacks=lambda: FakeResp(
            [
                {
                    "id": "st1",
                    "name": "Stack",
                    "policyset_ids": ["ns1"],
                    "default_policysetstack": True,
                }
            ]
        ),
        networkpolicysets=lambda: FakeResp(
            [{"id": f"path{i}", "name": f"Path-{i}"} for i in range(12)]
        ),
        networkpolicyrules=lambda networkpolicyset_id: FakeResp([]),
        networkpolicysetstacks=lambda: FakeResp([]),
    )
    post = SimpleNamespace(
        events_query=lambda payload: FakeResp(
            content={"items": EVENTS, "total_count": len(EVENTS)}
        ),
        query_auditlog=lambda payload: FakeResp(
            [{"operator_email": "a@b.c", "request_uri": "/x", "response_code": 200}]
            if auditlog_status == 200
            else None,
            status_code=auditlog_status,
        ),
        query_upgrade_status=lambda payload: FakeResp([{"id": "job1"}]),
        anynetlinks_query=lambda payload: FakeResp(ANYNETLINKS),
        monitor_metrics=monitor_metrics,
    )
    return SimpleNamespace(get=get, post=post)


@pytest.fixture
def tools(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    fake_sdk = make_fake_sdk()
    monkeypatch.setattr(sdwan_tools, "get_tenant_meta", lambda tid: SimpleNamespace(tenant_id=tid))
    monkeypatch.setattr(sdwan_tools, "list_loaded_tenants", lambda: ["t1"])
    monkeypatch.setattr(sdwan_tools, "get_sdwan_client", lambda tc: fake_sdk)
    mcp = FastMCP("test")
    sdwan_tools.register_sdwan_tools(mcp, None)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


def test_new_tools_register(tools: dict[str, Any]) -> None:
    assert {
        "sdwan_events",
        "sdwan_audit_logs",
        "sdwan_software_status",
        "sdwan_policy_rules",
        "sdwan_link_health",
    } <= set(tools)


def test_events_summary_and_code_resolution(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_events"]())
    assert data["summary"]["returned"] == 2
    assert data["summary"]["active_not_cleared"] == 1
    assert data["summary"]["by_severity"] == {"major": 2}
    ev = data["events"][0]
    assert ev["display_name"] == "Interface Down"
    assert ev["site_name"] == "Branch-1"
    assert ev["element_name"] == "ion-1"


def test_events_exclude_cleared(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_events"](include_cleared=False))
    assert data["summary"]["returned"] == 1
    assert all(not e["cleared"] for e in data["events"])


def test_audit_logs_ok(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_audit_logs"]())
    assert data["total"] == 1
    assert data["audit_logs"][0]["operator_email"] == "a@b.c"


def test_audit_logs_403_rbac_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_sdk = make_fake_sdk(auditlog_status=403)
    monkeypatch.setattr(sdwan_tools, "get_tenant_meta", lambda tid: SimpleNamespace(tenant_id=tid))
    monkeypatch.setattr(sdwan_tools, "list_loaded_tenants", lambda: ["t1"])
    monkeypatch.setattr(sdwan_tools, "get_sdwan_client", lambda tc: fake_sdk)
    mcp = FastMCP("test")
    sdwan_tools.register_sdwan_tools(mcp, None)
    out = mcp._tool_manager.get_tool("sdwan_audit_logs").fn()
    assert "403" in out and "role" in out


def test_software_status_histogram_and_pending(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_software_status"]())
    assert data["version_histogram"] == {"6.5.2-b2": 1, "6.1.4-b2": 1}
    e1 = next(e for e in data["elements"] if e["element_id"] == "e1")
    # the record with the highest _updated_on_utc wins, and a staged image
    # that differs from the active one means an upgrade is pending
    assert e1["software_status"]["upgrade_pending"] is True
    assert e1["software_status"]["upgrade_state"] == "download_cancelled"
    assert e1["machine_state"] == "claimed"
    assert [m["machine_id"] for m in data["machines_unclaimed"]] == ["m2"]
    assert data["upgrade_jobs"] == [{"id": "job1"}]


def test_policy_rules_nat(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_policy_rules"](policy_type="nat"))
    assert data["total_sets"] == 1
    assert data["policy_set_stacks"][0]["default"] is True
    rules = data["rules_by_set"]["NAT-Set"]
    assert rules[0]["actions"] == [{"type": "source_nat_dynamic"}]


def test_policy_rules_many_sets_need_set_id(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_policy_rules"](policy_type="path"))
    assert data["total_sets"] == 12
    assert data["rules_by_set"] == {}
    assert "policy_set_id" in data["note"]


def test_policy_rules_unknown_type(tools: dict[str, Any]) -> None:
    out = tools["sdwan_policy_rules"](policy_type="bogus")
    assert out.startswith("Error:") and "policy_type" in out


def test_link_health_requires_site(tools: dict[str, Any]) -> None:
    assert "site_id is required" in tools["sdwan_link_health"]()


def test_link_health_paths_and_stats(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_link_health"](site_id="s1"))
    # only p1 touches s1
    assert data["total_paths"] == 1
    assert data["paths"][0]["remote_site"] == "DC-1"
    by_metric = {r["metric"] for r in data["link_quality"]}
    assert by_metric == {"LqmLatency", "LqmJitter"}
    lat = next(r for r in data["link_quality"] if r["metric"] == "LqmLatency")
    assert (lat["min"], lat["avg"], lat["max"]) == (10.0, 15.0, 20.0)
    assert lat["path_id"] == "p1" and lat["remote_site"] == "DC-1"
    bw = data["bandwidth"][0]
    assert bw["metric"] == "BandwidthUsage" and bw["unit"] == "Mbps"


def test_site_map_writes_html_and_skips_unlocated(tools: dict[str, Any], tmp_path: Any) -> None:
    out = tmp_path / "map.html"
    result = tools["sdwan_site_map"](tenant_id="t1", save_to=str(out))
    assert "1 sites mapped" in result and "DC-1" in result  # skipped by name
    html = out.read_text()
    assert "Branch-1" in html and '"lat": 51.5' in html
    assert "Circuit-1 (BT-INET)" in html
    assert "leaflet" in html


def test_link_health_caps_paths(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_link_health"](site_id="s2", max_paths=1))
    assert data["total_paths"] == 2
    # admin-up path queried first, cap of 1 → only p1 in link_quality
    assert {r["path_id"] for r in data["link_quality"]} == {"p1"}
