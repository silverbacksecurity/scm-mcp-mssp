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


APPDEFS = [
    {"id": "app-dns", "display_name": "dns-base"},
    {"id": "app-ssl", "display_name": "ssl"},
]
FLOW_ITEMS = [
    {
        "source_ip": "172.16.0.1",
        "destination_ip": "8.8.8.8",
        "destination_port": 53,
        "app_id": "app-dns",
        "bytes_c2s": 58,
        "bytes_s2c": 100,
        "flow_action": "flow_drop",
        "path_type": "PrivateWAN",
    },
    {
        "source_ip": "172.16.0.2",
        "destination_ip": "1.1.1.1",
        "destination_port": 443,
        "app_id": "app-ssl",
        "bytes_c2s": 5000,
        "bytes_s2c": 90000,
        "flow_action": "flow_allow",
        "path_type": "DirectInternet",
    },
]
CELLULAR_MODULES = [
    {
        "id": "cm1",
        "name": "cwan1",
        "element_id": "e1",
        "radio_on": True,
        "gps_enable": True,
        "primary_sim": 1,
    },
    {
        "id": "cm2",
        "name": "cwan1",
        "element_id": "e2",
        "radio_on": False,
        "gps_enable": False,
        "primary_sim": 1,
    },
]
CELLULAR_STATUS = [
    {
        "id": "cs1",
        "cellular_module_id": "cm1",
        "element_id": "e1",
        "model_name": "EM7421",
        "manufacturer": "Sierra Wireless",
        "imei": "356281110210735",
        "modem_state": "online",
        "carrier": "EE",
        "technology": "LTE",
        "signal_strength_indicator": "excellent",
        "network_registration_state": "registered",
        "packet_service_state": "attached",
        "activation_state": "activated",
        "active_sim": 1,
        "network_state": {"roaming": False},
        "sim": [{"slot_number": 1, "present": True, "carrier": "EE", "pin_state": "disabled"}],
        "firmware": [
            {"fw_version": "01.14.03.00", "active": True},
            {"fw_version": "01.09.00.00", "active": False},
        ],
    }
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
        appdefs=lambda: FakeResp(APPDEFS),
    )

    def monitor_topn(payload: dict[str, Any]) -> FakeResp:
        kind = payload["top_n"]["type"]
        items = ["app-ssl", "app-dns"] if kind == "app" else ["s1", "s2"]
        return FakeResp(content={"top_n": {"type": kind, "items": items}})

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
        monitor_flows=lambda payload: FakeResp(content={"flows": {"items": FLOW_ITEMS}}),
        monitor_aggregates_healthscore=lambda payload: FakeResp(
            content={
                "items": [
                    {"health": "good", "count": 8, "data": []},
                    {"health": "poor", "count": 1, "data": []},
                ]
            }
        ),
        monitor_topn=monitor_topn,
        monitor_applicationsummary_query=lambda payload: FakeResp(
            content={
                "response": [
                    {
                        "app_id": "app-ssl",
                        "application_healthscore_avg": 9.5,
                        "site_id": "s1",
                        "duration": "2026-07-12T00:00:00Z",
                    }
                ]
            }
        ),
        cellular_modules_query=lambda payload: FakeResp(CELLULAR_MODULES),
        cellular_modules_status_query=lambda payload: FakeResp(CELLULAR_STATUS),
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


# ── Round 2: flows / app health / cellular ──────────────────────────────────


def test_flows_requires_site(tools: dict[str, Any]) -> None:
    assert "site_id is required" in tools["sdwan_flows"]()


def test_flows_top_talkers(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_flows"](site_id="s1"))
    assert data["site_name"] == "Branch-1"
    assert data["total_flows"] == 2
    assert data["dropped_flows"] == 1
    # ssl flow is 95000 bytes vs dns 158 — must rank first, name resolved
    assert data["top_applications"][0] == {"key": "ssl", "flows": 1, "bytes": 95000}
    assert data["top_sources"][0]["key"] == "172.16.0.2"
    assert data["top_destinations"][0]["key"] == "1.1.1.1:443"
    assert {p["key"] for p in data["path_types"]} == {"DirectInternet", "PrivateWAN"}


def test_flows_top_cap(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_flows"](site_id="s1", top=1))
    assert len(data["top_applications"]) == 1
    assert len(data["top_destinations"]) == 1


def test_app_health_buckets_and_topn(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_app_health"]())
    assert data["healthscore"]["Site"] == {"good": 8, "poor": 1}
    assert set(data["healthscore"]) == {"Site", "Circuit", "AnynetLink"}
    assert [a["app"] for a in data["top_applications"]] == ["ssl", "dns-base"]
    assert [s["site"] for s in data["top_sites"]] == ["Branch-1", "DC-1"]
    assert data["app_healthscores"][0]["app"] == "ssl"
    assert data["app_healthscores"][0]["healthscore_avg"] == 9.5
    assert data["app_healthscores"][0]["site"] == "Branch-1"


def test_app_health_site_scope_drops_top_sites(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_app_health"](site_id="s1"))
    assert data["top_sites"] == []
    assert data["top_applications"]


def test_app_health_invalid_basis(tools: dict[str, Any]) -> None:
    assert "basis must be one of" in tools["sdwan_app_health"](basis="bogus")


def test_cellular_status_joins_config_and_status(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_cellular_status"]())
    assert data["total"] == 2
    m1 = next(m for m in data["modules"] if m["module_id"] == "cm1")
    assert m1["element"] == "ion-1"
    assert m1["site"] == "Branch-1"
    assert m1["modem_state"] == "online"
    assert m1["carrier"] == "EE"
    assert m1["signal_strength"] == "excellent"
    assert m1["roaming"] is False
    assert m1["firmware"] == "01.14.03.00"  # active image only
    assert m1["sims"] == [{"slot": 1, "present": True, "carrier": "EE", "pin_state": "disabled"}]
    # module without a status record degrades to config-only fields
    m2 = next(m for m in data["modules"] if m["module_id"] == "cm2")
    assert m2["element"] == "ion-2"
    assert m2["modem_state"] is None


def test_cellular_status_element_filter(tools: dict[str, Any]) -> None:
    data = json.loads(tools["sdwan_cellular_status"](element_id="e2"))
    assert data["total"] == 1
    assert data["modules"][0]["module_id"] == "cm2"
