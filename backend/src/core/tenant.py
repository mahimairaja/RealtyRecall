"""Tenant routing helpers shared by the token mint, the call-close path, and the agent.

A LiveKit room name encodes the tenant as ``t_{tenant_id}_{random}``. tenant_id is the
Clerk organization id, which itself contains underscores (e.g. ``org_2ab...``), so decoding
strips the ``t_`` prefix and splits the trailing random suffix off the RIGHT. The random
suffix is uuid hex (no underscores), so the rpartition is unambiguous.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Header


def room_name_for_tenant(tenant_id: str) -> str:
    """Encode a tenant into a fresh room name."""
    return f"t_{tenant_id}_{uuid.uuid4().hex[:12]}"


def tenant_from_room_name(room: str | None) -> str | None:
    """Recover the tenant_id from a ``t_{tenant_id}_{random}`` room name, or None."""
    if not room or not room.startswith("t_"):
        return None
    tenant_id, _, suffix = room[2:].rpartition("_")
    if not tenant_id or not suffix:
        return None
    return tenant_id


async def get_agent_tenant_id(
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-Id")],
) -> str:
    """Agent requests carry the tenant in the X-Tenant-Id header (the agent derives it by
    parsing its room name). The realtor console uses get_current_tenant (Clerk JWT) instead.
    """
    return x_tenant_id
