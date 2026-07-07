import logging

import pytest

import src.core.tool_tracing as tracing
from src.core.tool_tracing import traced_tool


class _Obj:
    _tenant_id = "org_x"

    @traced_tool
    async def ok_tool(self, context, phone=None):
        return "a matching home at 88 Maple Ridge"

    @traced_tool
    async def bad_tool(self, context):
        raise RuntimeError("boom")


async def test_traced_tool_returns_and_logs_success_with_redaction(caplog):
    with caplog.at_level(logging.INFO, logger="agent"):
        out = await _Obj().ok_tool(None, phone="+15195550100")
    assert out == "a matching home at 88 Maple Ridge"  # return value passed through
    msg = next(r.getMessage() for r in caplog.records if "ok_tool" in r.getMessage())
    assert "ok" in msg and "latency_ms" in msg
    assert "+15195550100" not in msg and "***" in msg  # phone redacted


async def test_traced_tool_reraises_and_logs_failure(caplog):
    with caplog.at_level(logging.WARNING, logger="agent"):
        with pytest.raises(RuntimeError):
            await _Obj().bad_tool(None)
    assert any(
        "FAILED" in r.getMessage() and "bad_tool" in r.getMessage()
        for r in caplog.records
    )


async def test_traced_tool_adds_a_sentry_breadcrumb(monkeypatch):
    crumbs: list[dict] = []
    monkeypatch.setattr(
        tracing.sentry_sdk, "add_breadcrumb", lambda **kw: crumbs.append(kw)
    )
    await _Obj().ok_tool(None)
    assert crumbs and crumbs[0]["category"] == "tool"
    assert crumbs[0]["message"] == "ok_tool" and crumbs[0]["level"] == "info"
