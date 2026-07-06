"""Fast buyer-profile persistence (own Database, no DI), mirroring tenant_repository.

The profile is a small structured row keyed by (tenant_id, phone), written on
capture_lead and read at call start. It is the hot cache that lets the assistant
recognize a returning buyer instantly; Cognee remains the system of record for
deep multi-hop recall.
"""

from __future__ import annotations

from sqlmodel import select

from src.core.config import config
from src.core.database import Database
from src.models.buyer_profile_model import BuyerProfile

_db: Database | None = None


def _database() -> Database:
    global _db
    if _db is None:
        _db = Database(config)
    return _db


async def get(tenant_id: str, phone: str) -> BuyerProfile | None:
    async with _database().session() as session:
        result = await session.execute(
            select(BuyerProfile).where(
                BuyerProfile.tenant_id == tenant_id,
                BuyerProfile.phone == phone,
            )
        )
        return result.scalars().first()


async def upsert(
    tenant_id: str,
    phone: str,
    *,
    name: str | None = None,
    budget: str | None = None,
    area: str | None = None,
    prefs_summary: str | None = None,
) -> BuyerProfile:
    """Insert-or-update the profile for (tenant_id, phone). Only fields that were
    actually provided are written, so a later partial capture_lead (e.g. just a new
    area) never wipes a name we already stored."""
    async with _database().session() as session:
        result = await session.execute(
            select(BuyerProfile).where(
                BuyerProfile.tenant_id == tenant_id,
                BuyerProfile.phone == phone,
            )
        )
        obj = result.scalars().first()
        if obj is None:
            obj = BuyerProfile(tenant_id=tenant_id, phone=phone)
            session.add(obj)
        for field, value in (
            ("name", name),
            ("budget", budget),
            ("area", area),
            ("prefs_summary", prefs_summary),
        ):
            if value is not None:
                setattr(obj, field, value)
        await session.commit()
        await session.refresh(obj)
        return obj
