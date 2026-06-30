from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import src.api.endpoints.recall as recall_mod
from src.core.tenant import get_agent_tenant_id

TENANT = "org_recall_test"


class _FakeStore:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def recall(self, tenant_id, criteria, top_k=5):
        self.calls.append(tenant_id)
        return ["A matching 3 bed home at 123 Maple Street, Sarnia"]


def _client(monkeypatch, store=None) -> AsyncClient:
    monkeypatch.setattr(recall_mod, "get_memory_store", lambda: store or _FakeStore())
    app = FastAPI()
    app.include_router(recall_mod.router, prefix="/api/v1")
    # Stand in for the agent-secret-gated tenant so the test does not need the header.
    app.dependency_overrides[get_agent_tenant_id] = lambda: TENANT
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_recall_returns_grounded_answer(monkeypatch):
    store = _FakeStore()
    async with _client(monkeypatch, store) as c:
        resp = await c.post(
            "/api/v1/recall",
            json={"realtor": "Riley", "criteria": {"area": "Sarnia", "minBeds": 3}},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["realtor"] == "Riley"
    assert "Maple" in body["answer"]
    assert body["match_count"] == 1
    # The recall was scoped to the agent's asserted tenant.
    assert store.calls == [TENANT]


async def test_recall_accepts_free_text_criteria(monkeypatch):
    async with _client(monkeypatch) as c:
        resp = await c.post(
            "/api/v1/recall",
            json={"realtor": "Riley", "criteria": "3 bedroom near the park"},
        )
    assert resp.status_code == 200
    assert resp.json()["answer"]


async def test_recall_without_agent_secret_is_rejected(monkeypatch):
    # No dependency override: a caller that asserts a tenant but cannot present the shared
    # agent secret must be refused rather than allowed to read that tenant's listings.
    monkeypatch.setattr(recall_mod, "get_memory_store", lambda: _FakeStore())
    app = FastAPI()
    app.include_router(recall_mod.router, prefix="/api/v1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        resp = await c.post(
            "/api/v1/recall",
            headers={"X-Tenant-Id": "org_victim"},
            json={"realtor": "Riley", "criteria": "3 bed"},
        )
    assert resp.status_code == 401
