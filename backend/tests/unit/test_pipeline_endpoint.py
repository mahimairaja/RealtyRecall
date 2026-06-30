import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import src.api.endpoints.pipeline as pipeline_mod
import src.core.widget_guard as widget_guard


class _B:
    id = 1
    address = "1 Main St"
    status = "accepted"
    start_utc = None
    phone = "+1519"


class _C:
    id = 2
    room_name = "r1"
    outcome = "completed"
    buyer_phone = "+1519"
    ended_at = None


@pytest.fixture(autouse=True)
def _reset_limiter():
    widget_guard._limiter = None
    yield
    widget_guard._limiter = None


async def test_pipeline_returns_bookings_and_calls(monkeypatch):
    async def fake_bookings(limit: int = 20):
        return [_B()]

    async def fake_calls(limit: int = 20):
        return [_C()]

    monkeypatch.setattr(pipeline_mod.booking_repository, "list_recent", fake_bookings)
    monkeypatch.setattr(pipeline_mod.call_log_repository, "list_recent", fake_calls)
    app = FastAPI()
    app.include_router(pipeline_mod.router, prefix="/api/v1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        resp = await c.get("/api/v1/pipeline")
    assert resp.status_code == 200
    body = resp.json()
    assert body["bookings"][0]["address"] == "1 Main St"
    assert body["bookings"][0]["status"] == "accepted"
    assert body["calls"][0]["room_name"] == "r1"
