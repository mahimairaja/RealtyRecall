import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from src.core import tenant as tenant_mod
from src.core.tenant import (
    get_agent_tenant_id,
    room_name_for_tenant,
    tenant_from_room_name,
)

# A realistic Clerk org id: it contains underscores, which is why decoding splits
# the random suffix off the RIGHT (rpartition), not the left.
ORG = "org_2abCDef_GhiJkl"


def test_room_name_encodes_and_round_trips_tenant():
    room = room_name_for_tenant(ORG)
    assert room.startswith(f"t_{ORG}_")
    assert tenant_from_room_name(room) == ORG


def test_room_names_are_unique_per_call():
    assert room_name_for_tenant(ORG) != room_name_for_tenant(ORG)


@pytest.mark.parametrize(
    "room",
    [None, "", "plain-room", "room-abc123", "t_", "t_onlytenant"],
)
def test_tenant_from_room_name_rejects_non_tenant_rooms(room):
    assert tenant_from_room_name(room) is None


def _set_secret(monkeypatch, value):
    monkeypatch.setattr(
        tenant_mod.config,
        "AGENT_SERVICE_SECRET",
        SecretStr(value) if value is not None else None,
    )


async def test_agent_tenant_id_accepts_matching_secret(monkeypatch):
    _set_secret(monkeypatch, "s3cret")
    assert await get_agent_tenant_id(ORG, "s3cret") == ORG


async def test_agent_tenant_id_rejects_wrong_secret(monkeypatch):
    _set_secret(monkeypatch, "s3cret")
    with pytest.raises(HTTPException) as exc:
        await get_agent_tenant_id(ORG, "nope")
    assert exc.value.status_code == 401


async def test_agent_tenant_id_rejects_missing_secret_header(monkeypatch):
    _set_secret(monkeypatch, "s3cret")
    with pytest.raises(HTTPException) as exc:
        await get_agent_tenant_id(ORG, None)
    assert exc.value.status_code == 401


async def test_agent_tenant_id_refuses_when_secret_unconfigured(monkeypatch):
    # With no AGENT_SERVICE_SECRET set, the endpoint must refuse rather than fail open.
    _set_secret(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        await get_agent_tenant_id(ORG, "anything")
    assert exc.value.status_code == 401
