"""Lean Tenant persistence, mirroring the booking/call_log repos (own Database, no DI).

The tenant boundary is ``clerk_org_id`` (the Clerk organization id). Tenants are upserted
lazily on the first authenticated console request.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from src.core.config import config
from src.core.database import Database
from src.models.tenant_model import Tenant

_db: Database | None = None


def _database() -> Database:
    global _db
    if _db is None:
        _db = Database(config)
    return _db


async def get_by_clerk_org_id(clerk_org_id: str) -> Tenant | None:
    async with _database().session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.clerk_org_id == clerk_org_id)
        )
        return result.scalars().first()


async def upsert(clerk_org_id: str, name: str | None = None) -> Tenant:
    """Insert-or-get a Tenant keyed by the unique clerk_org_id. Idempotent and
    concurrency-safe: a racing insert that hits the unique constraint falls back to a read.
    """
    existing = await get_by_clerk_org_id(clerk_org_id)
    if existing is not None:
        if name and existing.name != name:
            async with _database().session() as session:
                existing.name = name
                session.add(existing)
                await session.commit()
                await session.refresh(existing)
        return existing
    try:
        async with _database().session() as session:
            obj = Tenant(clerk_org_id=clerk_org_id, name=name)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj
    except IntegrityError:
        # Lost the insert race; the row now exists.
        found = await get_by_clerk_org_id(clerk_org_id)
        if found is None:
            raise
        return found
