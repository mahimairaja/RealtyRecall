"""Match a newly connected listing to waiting buyers (REQ-RR-MEM-002).

Thin wrapper over the memory store's graph search, scoped to one realtor (tenant): matching
runs over the typed Buyer nodes in that tenant's NodeSet, so a new home is only ever matched
against the same realtor's waiting buyers.
"""

from __future__ import annotations

from typing import Any

from src.memory.store import get_memory_store


async def find_matches(tenant_id: str, listing: dict[str, Any]) -> dict[str, Any]:
    summary = await get_memory_store().match_buyers(tenant_id, listing)
    return {"summary": summary, "matched": bool(summary)}
