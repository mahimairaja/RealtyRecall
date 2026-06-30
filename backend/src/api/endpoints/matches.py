from fastapi import APIRouter

from src.core.clerk import CurrentTenant
from src.schemas.match_schemas import MatchRequest, MatchResponse
from src.services import matching_service

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=MatchResponse)
async def find_matches(
    payload: MatchRequest,
    tenant_id: CurrentTenant,
) -> MatchResponse:
    # The realtor's "who wants this new home" view: matches a connected listing against the
    # signed-in realtor's own waiting buyers (scoped to their tenant NodeSet).
    result = await matching_service.find_matches(tenant_id, payload.model_dump())
    return MatchResponse(**result)
