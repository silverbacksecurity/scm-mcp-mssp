"""Tests for the SP Interconnect and PAB-for-MSP tool modules (no network)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from scm_mcp_mssp.tools.mt_interconnect import _render as spi_render
from scm_mcp_mssp.tools.mt_interconnect import register_spi_tools
from scm_mcp_mssp.tools.pab_msp import _render as pab_render
from scm_mcp_mssp.tools.pab_msp import register_pab_msp_tools


def _mcp_with_tools() -> FastMCP:
    mcp = FastMCP("test")
    register_spi_tools(mcp, lambda tenant_id="": None)
    register_pab_msp_tools(mcp, lambda tenant_id="": None)
    return mcp


def test_tools_register() -> None:
    mcp = _mcp_with_tools()
    names = set(mcp._tool_manager._tools)
    assert {"scm_spi_status", "scm_pab_msp_summary", "scm_pab_msp_report"} <= names


def test_spi_rejects_unknown_view_before_client_resolution() -> None:
    mcp = _mcp_with_tools()
    out = mcp._tool_manager.get_tool("scm_spi_status").fn(view="bogus")
    assert "Unknown view" in out and "summary" in out


def test_pab_report_validation() -> None:
    mcp = _mcp_with_tools()
    report = mcp._tool_manager.get_tool("scm_pab_msp_report").fn
    assert "Unknown report" in report(report="nope", tsg_id="123")
    assert "required" in report(report="count")


def test_pab_summary_rejects_unknown_scope() -> None:
    mcp = _mcp_with_tools()
    out = mcp._tool_manager.get_tool("scm_pab_msp_summary").fn(scope="bogus")
    assert "Unknown scope" in out


def test_render_branches() -> None:
    for render, hint in ((spi_render, "MSP role"), (pab_render, "MSP role")):
        assert hint in render("t", "https://u", 403, None)
        assert "404" in render("t", "https://u", 404, None)
        assert "body suppressed" in render("t", "https://u", 500, "<html>stack</html>")
        ok = render("t", "https://u", 200, {"data": [{"id": 1}]})
        assert ok.startswith("# t (1)") and '"id": 1' in ok


def test_render_truncates_large_payloads() -> None:
    big = {"data": [{"x": "y" * 100} for _ in range(500)]}
    out = spi_render("t", "https://u", 200, big)
    assert "truncated" in out
