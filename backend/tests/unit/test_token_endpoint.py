import base64
import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from livekit.api import TokenVerifier

import src.core.widget_guard as widget_guard
from src.api.endpoints.token import router as token_router
from src.core.config import Config
from src.core.container import Container
from src.services.token_service import TokenService

KEY = "devkey"
SECRET = "devsecret-devsecret-devsecret-1234"
URL = "wss://example.livekit.cloud"


@pytest.fixture(autouse=True)
def _reset_widget_limiter():
    # The limiter is a module global keyed by client IP; all test requests share one IP.
    widget_guard._limiter = None
    yield
    widget_guard._limiter = None


def _cfg(**over) -> Config:
    base: dict = {
        "ENV": "dev",
        "_env_file": None,
        "LIVEKIT_URL": URL,
        "LIVEKIT_API_KEY": KEY,
        "LIVEKIT_API_SECRET": SECRET,
    }
    base.update(over)
    return Config(**base)


async def _request_token(cfg, monkeypatch, *, headers=None, body=None):
    # The guard reads get_config() directly; point it at this test config.
    monkeypatch.setattr(widget_guard, "get_config", lambda: cfg)
    container = Container()
    container.token_service.override(TokenService(cfg))
    container.wire(modules=["src.api.endpoints.token"])
    app = FastAPI()
    app.include_router(token_router, prefix="/api/v1")
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            return await c.post(
                "/api/v1/token",
                headers=headers or {},
                json=body if body is not None else {},
            )
    finally:
        container.unwire()


def _jwt_payload(token: str) -> dict:
    segment = token.split(".")[1]
    segment += "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment))


async def test_post_token_returns_201_with_valid_token(monkeypatch):
    resp = await _request_token(
        _cfg(), monkeypatch, body={"room_name": "demo", "participant_identity": "bob"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["server_url"] == URL
    claims = TokenVerifier(KEY, SECRET).verify(body["participant_token"])
    assert claims.identity == "bob"
    assert claims.video.room == "demo"


async def test_post_token_empty_body_uses_defaults(monkeypatch):
    resp = await _request_token(_cfg(), monkeypatch, body={})
    assert resp.status_code == 201
    assert resp.json()["participant_token"]


async def test_token_allowed_origin_is_accepted(monkeypatch):
    cfg = _cfg(WIDGET_ALLOWED_ORIGINS_STR="https://realtyrecall.example")
    resp = await _request_token(
        cfg, monkeypatch, headers={"origin": "https://realtyrecall.example"}, body={}
    )
    assert resp.status_code == 201


async def test_token_disallowed_origin_is_forbidden(monkeypatch):
    cfg = _cfg(WIDGET_ALLOWED_ORIGINS_STR="https://realtyrecall.example")
    resp = await _request_token(
        cfg, monkeypatch, headers={"origin": "https://evil.example"}, body={}
    )
    assert resp.status_code == 403
    assert "participant_token" not in resp.json()


async def test_token_empty_allowlist_allows_any_origin(monkeypatch):
    resp = await _request_token(
        _cfg(), monkeypatch, headers={"origin": "https://whatever.example"}, body={}
    )
    assert resp.status_code == 201


async def test_token_missing_origin_with_allowlist_is_forbidden(monkeypatch):
    cfg = _cfg(WIDGET_ALLOWED_ORIGINS_STR="https://realtyrecall.example")
    resp = await _request_token(cfg, monkeypatch, body={})
    assert resp.status_code == 403


async def test_token_rate_limit_returns_429(monkeypatch):
    cfg = _cfg(WIDGET_TOKEN_RATELIMIT_PER_MIN=1)
    first = await _request_token(cfg, monkeypatch, body={})
    assert first.status_code == 201
    second = await _request_token(cfg, monkeypatch, body={})
    assert second.status_code == 429


async def test_token_carries_short_ttl(monkeypatch):
    resp = await _request_token(_cfg(), monkeypatch, body={})
    assert resp.status_code == 201
    payload = _jwt_payload(resp.json()["participant_token"])
    base = payload.get("nbf") or payload.get("iat")
    assert base is not None
    assert payload["exp"] - base == 300
