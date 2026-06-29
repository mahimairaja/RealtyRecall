"""Live integration tests for the Cognee memory store.

Requires the stack up (Neo4j + pgvector Postgres) and OpenAI. Run via
`task gate:integration` or `pytest -m integration`. The fast gate skips these.

Cognee keeps a process-wide async engine bound to the first event loop it runs on,
so the stateful memory operations share one async test (one loop) rather than several.
"""

import uuid

import pytest

from src.memory.store import buyer_dataset, get_memory_store

pytestmark = pytest.mark.integration


async def test_memory_lifecycle_add_recall_upsert_forget():
    store = get_memory_store()
    tag = uuid.uuid4().hex[:8]

    # add a connected listing, then recall by criteria surfaces it
    await store.add_listings(
        {"name": "Riley Realtor", "email": "riley@example.com"},
        [
            {
                "code": f"L-{tag}",
                "address": f"{tag} Maple Street, Sarnia",
                "price": 450000,
                "beds": 3,
                "baths": 2,
                "description": "Charming 3 bed bungalow near the park",
                "area": "Sarnia",
            }
        ],
    )
    results = await store.recall({"area": "Sarnia", "minBeds": 3}, top_k=5)
    assert results, "recall returned no results for connected Sarnia listings"

    # upsert a buyer into its own dataset, then forget removes exactly that buyer
    phone = "+1-519-555-0142"
    await store.upsert_buyer(
        {"phone": phone, "name": "Dana", "criteria": {"area": "Sarnia", "minBeds": 2}}
    )
    result = await store.forget_buyer(phone)
    assert isinstance(result, dict)


def test_buyer_dataset_normalises_phone():
    assert buyer_dataset("+1 (519) 555-0142") == "buyer-15195550142"
    assert buyer_dataset("5195550142") == "buyer-5195550142"
