"""Integration: GET /pipeline reads recent bookings + calls from the real DB."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.endpoints.pipeline import router as pipeline_router
from src.core.clerk import get_current_tenant

pytestmark = pytest.mark.integration

TENANT = "org_pipeline_integration"


async def test_pipeline_reads_recent_rows():
    app = FastAPI()
    app.include_router(pipeline_router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant] = lambda: TENANT
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        resp = await c.get("/api/v1/pipeline")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["bookings"], list)
    assert isinstance(body["calls"], list)
