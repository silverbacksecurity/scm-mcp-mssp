"""Unit tests for utils.ipenrich — IP filtering, provider normalisation,
caching, and graceful degradation. All HTTP is monkeypatched; no I/O.

Note: fixtures use real global IPs (8.8.8.8 etc.) rather than RFC 5737
TEST-NET ranges, because TEST-NET is *reserved* and global_ips() correctly
filters it out — pinned in test_reserved_ranges_dropped.
"""

from __future__ import annotations

from typing import Any

import pytest

from scm_mcp_mssp.utils import ipenrich


@pytest.fixture(autouse=True)
def _clear_cache(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    ipenrich._cache.clear()
    ipenrich._disk_loaded = False
    monkeypatch.setattr(ipenrich, "_cache_path", lambda: tmp_path / "ipenrich.json")


class TestGlobalIps:
    def test_strips_cidr_suffix(self) -> None:
        assert ipenrich.global_ips(["8.8.8.8/30"]) == ["8.8.8.8"]

    def test_drops_private_loopback_linklocal_cgnat(self) -> None:
        assert (
            ipenrich.global_ips(
                ["10.0.0.1", "192.168.1.1/24", "127.0.0.1", "169.254.1.1", "100.64.0.1"]
            )
            == []
        )

    def test_reserved_ranges_dropped(self) -> None:
        # RFC 5737 documentation ranges are reserved, not global
        assert ipenrich.global_ips(["203.0.113.5/30", "198.51.100.9"]) == []

    def test_drops_garbage_and_empty(self) -> None:
        assert ipenrich.global_ips(["", "not-an-ip", None, "dhcp"]) == []  # type: ignore[list-item]

    def test_dedupes_preserving_order(self) -> None:
        assert ipenrich.global_ips(["8.8.8.8/30", "1.1.1.1", "8.8.8.8"]) == [
            "8.8.8.8",
            "1.1.1.1",
        ]

    def test_global_ipv6_kept(self) -> None:
        assert ipenrich.global_ips(["2606:4700::1111/128", "fe80::1"]) == ["2606:4700::1111"]


class _Resp:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


_IP_API_ROW = {
    "status": "success",
    "query": "8.8.8.8",
    "reverse": "dns.google",
    "isp": "Example Broadband",
    "org": "Example Networks Ltd",
    "as": "AS64500 Example Networks Ltd",
    "asname": "EXAMPLE-NET",
    "city": "London",
    "regionName": "England",
    "country": "United Kingdom",
    "lat": 51.5074,
    "lon": -0.1278,
}


class TestEnrichIpApi:
    def test_normalised_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ipenrich.requests, "post", lambda *a, **k: _Resp([_IP_API_ROW]))
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8/30"], provider="ip-api")
        assert warnings == []
        rec = by_ip["8.8.8.8"]
        assert rec["isp"] == "Example Broadband"
        assert rec["asn"] == "AS64500"
        assert rec["as_name"] == "EXAMPLE-NET"
        assert rec["reverse_dns"] == "dns.google"
        assert rec["country"] == "United Kingdom"
        assert rec["latitude"] == 51.5074
        assert rec["source"] == "ip-api.com"

    def test_failed_row_becomes_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rows = [{"status": "fail", "message": "rate limited", "query": "8.8.8.8"}]
        monkeypatch.setattr(ipenrich.requests, "post", lambda *a, **k: _Resp(rows))
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert by_ip == {}
        assert warnings == ["8.8.8.8: rate limited"]

    def test_private_only_input_makes_no_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _boom(*a: Any, **k: Any) -> Any:
            raise AssertionError("no HTTP expected")

        monkeypatch.setattr(ipenrich.requests, "post", _boom)
        assert ipenrich.enrich_public_ips(["10.0.0.1/24"], provider="ip-api") == ({}, [])

    def test_provider_down_degrades_to_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _boom(*a: Any, **k: Any) -> Any:
            raise ConnectionError("dns failure")

        monkeypatch.setattr(ipenrich.requests, "post", _boom)
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert by_ip == {}
        assert len(warnings) == 1 and "ip-api" in warnings[0]

    def test_second_call_served_from_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[Any] = []

        def _post(*a: Any, **k: Any) -> Any:
            calls.append(a)
            return _Resp([_IP_API_ROW])

        monkeypatch.setattr(ipenrich.requests, "post", _post)
        ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        by_ip, _ = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert len(calls) == 1
        assert by_ip["8.8.8.8"]["asn"] == "AS64500"

    def test_unknown_provider_is_warning_not_crash(self) -> None:
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="nonsense")
        assert by_ip == {}
        assert "nonsense" in warnings[0]


class TestDiskCache:
    def test_fetch_persists_and_new_process_reads_it(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ipenrich.requests, "post", lambda *a, **k: _Resp([_IP_API_ROW]))
        ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert ipenrich._cache_path().exists()

        # simulate a fresh process: memory gone, disk remains
        ipenrich._cache.clear()
        ipenrich._disk_loaded = False

        def _boom(*a: Any, **k: Any) -> Any:
            raise AssertionError("should be served from disk cache")

        monkeypatch.setattr(ipenrich.requests, "post", _boom)
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert warnings == []
        assert by_ip["8.8.8.8"]["asn"] == "AS64500"

    def test_expired_disk_entry_refetched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import json as _json
        import time as _time

        stale = {
            "ip-api|8.8.8.8": {
                "ts": _time.time() - ipenrich._CACHE_TTL - 1,
                "record": {"ip": "8.8.8.8", "asn": "AS-STALE"},
            }
        }
        ipenrich._cache_path().write_text(_json.dumps(stale))
        monkeypatch.setattr(ipenrich.requests, "post", lambda *a, **k: _Resp([_IP_API_ROW]))
        by_ip, _ = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert by_ip["8.8.8.8"]["asn"] == "AS64500"

    def test_corrupt_cache_file_degrades_silently(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ipenrich._cache_path().write_text("{not json")
        monkeypatch.setattr(ipenrich.requests, "post", lambda *a, **k: _Resp([_IP_API_ROW]))
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        assert warnings == []
        assert by_ip["8.8.8.8"]["asn"] == "AS64500"

    def test_providers_do_not_share_entries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ipenrich.requests, "post", lambda *a, **k: _Resp([_IP_API_ROW]))
        ipenrich.enrich_public_ips(["8.8.8.8"], provider="ip-api")
        calls: list[Any] = []

        def _get(*a: Any, **k: Any) -> Any:
            calls.append(a)
            return _Resp({"ip": "8.8.8.8", "org": "AS1 X"})

        monkeypatch.setattr(ipenrich.requests, "get", _get)
        ipenrich.enrich_public_ips(["8.8.8.8"], provider="ipinfo")
        assert len(calls) == 1  # ip-api entry must not satisfy ipinfo lookup


class TestEnrichIpinfo:
    def test_org_and_loc_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        payload = {
            "ip": "8.8.8.8",
            "hostname": "dns.google",
            "city": "Manchester",
            "region": "England",
            "country": "GB",
            "loc": "53.4808,-2.2426",
            "org": "AS64500 Example Networks Ltd",
        }
        monkeypatch.setattr(ipenrich.requests, "get", lambda *a, **k: _Resp(payload))
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ipinfo")
        assert warnings == []
        rec = by_ip["8.8.8.8"]
        assert rec["asn"] == "AS64500"
        assert rec["org"] == "Example Networks Ltd"
        assert rec["latitude"] == 53.4808
        assert rec["longitude"] == -2.2426
        assert rec["source"] == "ipinfo.io"

    def test_http_error_is_per_ip_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ipenrich.requests, "get", lambda *a, **k: _Resp({}, status_code=429))
        by_ip, warnings = ipenrich.enrich_public_ips(["8.8.8.8"], provider="ipinfo")
        assert by_ip == {}
        assert warnings == ["8.8.8.8: ipinfo.io HTTP 429"]
