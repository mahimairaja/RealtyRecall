from fastapi import APIRouter

from src.core.tenant import AgentTenant
from src.memory.store import get_memory_store
from src.schemas.listing_schemas import RealtorProfile

router = APIRouter(prefix="/realtor", tags=["realtor"])


@router.get("", response_model=RealtorProfile)
async def get_realtor(tenant_id: AgentTenant) -> RealtorProfile:
    # Agent-gated (agent-secret, not Clerk): the live voice assistant reads the realtor's
    # synthesized persona at call start so it can answer in their name and voice. Returns an
    # all-null profile when nothing is connected yet, so the agent degrades to a generic voice.
    persona = await get_memory_store().get_realtor(tenant_id) or {}
    return RealtorProfile(**persona)
