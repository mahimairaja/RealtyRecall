import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import src.api.endpoints.buyers as buyers_mod
from src.core.clerk import get_current_tenant
from src.core.tenant import get_agent_tenant_id

TENANT = "org_buyers_test"


class _Prof:
    def __init__(self, name=None, budget=None, area=None, prefs_summary=None) -> None:
        self.name = name
        self.budget = budget
        self.area = area
        self.prefs_summary = prefs_summary


class _FakeProfileRepo:
    def __init__(self) -> None:
        self.upserts: list[dict] = []
        self.stored: dict[tuple[str, str], _Prof] = {}

    async def upsert(
        self, tenant_id, phone, *, name=None, area=None, budget=None, prefs_summary=None
    ):
        self.upserts.append(
            {
                "tenant_id": tenant_id,
                "phone": phone,
                "name": name,
                "area": area,
                "budget": budget,
                "prefs_summary": prefs_summary,
            }
        )

    async def get(self, tenant_id, phone):
        return self.stored.get((tenant_id, phone))


@pytest.fixture(autouse=True)
def profile_repo(monkeypatch):
    """Stub the fast profile repo for every test so the dual-write never hits a DB."""
    repo = _FakeProfileRepo()
    monkeypatch.setattr(buyers_mod, "buyer_profile_repository", repo)
    return repo


class _FakeStore:
    def __init__(self) -> None:
        self.upserts: list[tuple[str, dict]] = []
        self.forgotten: tuple[str, str] | None = None

    async def upsert_buyer(self, tenant_id: str, buyer: dict) -> dict:
        self.upserts.append((tenant_id, buyer))
        return buyer

    async def get_buyer(self, tenant_id: str, phone: str) -> dict:
        if "0100" in phone:
            return {
                "found": True,
                "phone": phone,
                "summary": "Dana, looking in Sarnia for 3 bedrooms.",
            }
        return {"found": False, "phone": phone}

    async def recall_nearby(self, tenant_id: str, summary: str) -> None:
        return None

    async def forget_buyer(self, tenant_id: str, phone: str) -> dict:
        self.forgotten = (tenant_id, phone)
        return {"forgotten": True, "phone": phone}


def _client(monkeypatch, store) -> AsyncClient:
    monkeypatch.setattr(buyers_mod, "get_memory_store", lambda: store)
    app = FastAPI()
    app.include_router(buyers_mod.router, prefix="/api/v1")
    # Stand in for the agent-secret-gated tenant so the test does not need the header.
    app.dependency_overrides[get_agent_tenant_id] = lambda: TENANT
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_upsert_buyer(monkeypatch):
    store = _FakeStore()
    async with _client(monkeypatch, store) as c:
        resp = await c.post(
            "/api/v1/buyers",
            json={
                "phone": "+15195550100",
                "name": "Dana",
                "criteria": {"area": "Sarnia", "minBeds": 3},
            },
        )
    assert resp.status_code == 201
    assert resp.json()["phone"] == "+15195550100"
    assert store.upserts[0][0] == TENANT
    assert store.upserts[0][1]["name"] == "Dana"
    assert store.upserts[0][1]["criteria"]["area"] == "Sarnia"


async def test_get_known_buyer_returns_summary(monkeypatch):
    async with _client(monkeypatch, _FakeStore()) as c:
        resp = await c.get("/api/v1/buyers/+15195550100")
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is True
    assert "Sarnia" in body["summary"]


async def test_get_unknown_buyer_is_not_found(monkeypatch):
    async with _client(monkeypatch, _FakeStore()) as c:
        resp = await c.get("/api/v1/buyers/+15190000000")
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is False
    assert body["summary"] is None


async def test_forget_buyer(monkeypatch):
    store = _FakeStore()
    async with _client(monkeypatch, store) as c:
        resp = await c.delete("/api/v1/buyers/+15195550100")
    assert resp.status_code == 200
    assert resp.json()["forgotten"] is True
    assert store.forgotten == (TENANT, "+15195550100")


async def test_get_buyer_includes_a_nearby_suggestion_when_found(monkeypatch):
    class _Store:
        async def get_buyer(self, tenant_id, phone):
            return {
                "found": True,
                "phone": phone,
                "summary": "Dana liked a water-view bungalow.",
            }

        async def recall_nearby(self, tenant_id, summary):
            return "A new one on Cathcart just came up nearby."

    async with _client(monkeypatch, _Store()) as c:
        resp = await c.get("/api/v1/buyers/+15195550142")
    assert resp.status_code == 200
    assert resp.json()["nearby"] == "A new one on Cathcart just came up nearby."


async def test_list_buyers_is_console_scoped(monkeypatch):
    seen = {}

    class _Store:
        async def list_buyers(self, tenant_id):
            seen["tenant"] = tenant_id
            return [
                {
                    "phone": "+15195550100",
                    "name": "Dana",
                    "email": None,
                    "criteria": {"area": "Sarnia", "minBeds": 3},
                }
            ]

    monkeypatch.setattr(buyers_mod, "get_memory_store", lambda: _Store())
    app = FastAPI()
    app.include_router(buyers_mod.router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant] = lambda: "org_console"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        resp = await c.get("/api/v1/buyers")
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["name"] == "Dana"
    assert body[0]["criteria"]["area"] == "Sarnia"
    assert seen["tenant"] == "org_console"


async def test_upsert_also_writes_the_fast_profile(monkeypatch, profile_repo):
    async with _client(monkeypatch, _FakeStore()) as c:
        resp = await c.post(
            "/api/v1/buyers",
            json={
                "phone": "+15195550100",
                "name": "Dana",
                "criteria": {"area": "Sarnia", "minBeds": 3, "maxPrice": 480000},
            },
        )
    assert resp.status_code == 201
    row = profile_repo.upserts[0]
    assert row["tenant_id"] == TENANT and row["phone"] == "+15195550100"
    assert (
        row["name"] == "Dana" and row["area"] == "Sarnia" and row["budget"] == "480000"
    )
    assert "3+ beds" in row["prefs_summary"] and "Sarnia" in row["prefs_summary"]


async def test_get_buyer_profile_found_and_missing(monkeypatch, profile_repo):
    profile_repo.stored[(TENANT, "+15195550100")] = _Prof(
        name="Dana", area="Sarnia", prefs_summary="3+ beds, in Sarnia"
    )
    async with _client(monkeypatch, _FakeStore()) as c:
        found = await c.get("/api/v1/buyers/+15195550100/profile")
        missing = await c.get("/api/v1/buyers/+19999999999/profile")
    assert found.status_code == 200 and found.json()["found"] is True
    assert found.json()["name"] == "Dana" and found.json()["prefs_summary"]
    assert missing.json()["found"] is False and missing.json()["name"] is None
