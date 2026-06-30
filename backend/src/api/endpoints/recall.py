from typing import Any

from fastapi import APIRouter

from src.core.tenant import AgentTenant
from src.memory.store import get_memory_store
from src.schemas.recall_schemas import RecallRequest, RecallResponse

router = APIRouter(prefix="/recall", tags=["recall"])


def _first_answer(results: list[Any]) -> str:
    """Cognee recall returns grounded completion entries; pull the first answer text."""
    if not results:
        return ""
    first = results[0]
    for attr in ("answer", "text", "content"):
        value = getattr(first, attr, None)
        if isinstance(value, str) and value:
            return value
    return str(first)


# The agent calls this during a buyer call to find matching listings. It presents the tenant
# (X-Tenant-Id) and the shared agent secret, and the recall is scoped to that realtor's
# NodeSet, so cross-realtor homes never leak (verified live, see scripts/verify_tenant_isolation).
@router.post("", response_model=RecallResponse)
async def recall(
    payload: RecallRequest,
    tenant_id: AgentTenant,
) -> RecallResponse:
    results = await get_memory_store().recall(
        tenant_id, payload.criteria, top_k=payload.top_k
    )
    return RecallResponse(
        realtor=payload.realtor,
        answer=_first_answer(results),
        match_count=len(results),
    )
