"""Unit tests for scm_insights_query (tools/insights.py).

The tool had no tests when added; these pin URL construction per API
version, region resolution, body validation, error pass-through, and the
two fixes from review: OAuth refresh before direct-session calls and no
empty Prisma-Tenant header.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

from mcp.server.fastmcp import FastMCP

from scm_mcp_mssp.tools.insights import register_insights_tools


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post(self, url, json=None, headers=None, timeout=None):  # noqa: A002
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


def _client(session: FakeSession) -> Any:
    client = MagicMock()
    client.session = session
    client.oauth_client = MagicMock()
    return client


def _invoke(session: FakeSession, client: Any | None = None, **kwargs: Any) -> str:
    mcp = FastMCP("test-insights")
    the_client = client or _client(session)
    register_insights_tools(mcp, get_client=lambda tid="": the_client)
    tool = mcp._tool_manager.get_tool("scm_insights_query")
    return tool.fn(**kwargs)


class TestUrlConstruction:
    def test_v3_prefixes_query_segment(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(session, resource="gp_mobileusers/connected_user_count", tenant_id="123")
        assert session.calls[0]["url"] == (
            "https://api.sase.paloaltonetworks.com/insights/v3.0/resource"
            "/query/gp_mobileusers/connected_user_count"
        )

    def test_v2_uses_raw_resource_path(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(
            session,
            resource="custom/query/gp_mobileusers/connected_user_count",
            tenant_id="123",
            api_version="v2",
        )
        assert session.calls[0]["url"].startswith(
            "https://api.sase.paloaltonetworks.com/api/sase/v2.0/resource/custom/query/"
        )

    def test_leading_slash_is_tolerated(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(session, resource="/tunnels/tunnel_list", tenant_id="123")
        assert "/query/tunnels/tunnel_list" in session.calls[0]["url"]


class TestHeaders:
    def test_tenant_header_present_when_tenant_given(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(session, resource="x", tenant_id="1061891050")
        assert session.calls[0]["headers"]["Prisma-Tenant"] == "1061891050"

    def test_no_empty_tenant_header(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(session, resource="x", tenant_id="")
        assert "Prisma-Tenant" not in session.calls[0]["headers"]

    def test_region_override_wins(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(session, resource="x", tenant_id="1", region="americas")
        assert session.calls[0]["headers"]["X-PANW-Region"] == "americas"

    def test_token_refresh_attempted_before_call(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        client = _client(session)
        _invoke(session, client=client, resource="x", tenant_id="1")
        client.oauth_client.refresh_token.assert_called()


class TestBodyAndResults:
    def test_invalid_body_json_is_a_clear_error(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        out = _invoke(session, resource="x", tenant_id="1", body="{not json")
        assert out.startswith("Error: invalid JSON in `body`")
        assert session.calls == []  # nothing was sent

    def test_body_passed_through(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": []}))
        _invoke(session, resource="x", tenant_id="1", body='{"count": 5}')
        assert session.calls[0]["json"] == {"count": 5}

    def test_data_array_extracted_with_count(self) -> None:
        session = FakeSession(FakeResponse(payload={"data": [{"a": 1}, {"a": 2}]}))
        out = json.loads(_invoke(session, resource="x", tenant_id="1"))
        assert out["count"] == 2
        assert out["data"] == [{"a": 1}, {"a": 2}]

    def test_http_error_surfaces_status_and_detail(self) -> None:
        session = FakeSession(FakeResponse(status_code=403, payload=None, text="Forbidden"))
        out = json.loads(_invoke(session, resource="tunnels/tunnel_list", tenant_id="1"))
        assert out["error"] == "HTTP 403"
        assert "Forbidden" in out["detail"]
