from fastapi import APIRouter, Depends

from src.core.widget_guard import enforce_widget_guard
from src.repository import booking_repository, call_log_repository
from src.schemas.pipeline_schemas import (
    PipelineBooking,
    PipelineCall,
    PipelineResponse,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("", response_model=PipelineResponse)
async def pipeline(_: None = Depends(enforce_widget_guard)) -> PipelineResponse:
    # The realtor view: recent bookings and calls (the connected homes and tracked buyers
    # live in Cognee and are shown via the memory-graph visualization).
    bookings = await booking_repository.list_recent()
    calls = await call_log_repository.list_recent()
    return PipelineResponse(
        bookings=[
            PipelineBooking(
                id=b.id,
                address=b.address,
                status=b.status,
                start_utc=b.start_utc,
                phone=b.phone,
            )
            for b in bookings
        ],
        calls=[
            PipelineCall(
                id=c.id,
                room_name=c.room_name,
                outcome=c.outcome,
                buyer_phone=c.buyer_phone,
                ended_at=c.ended_at,
            )
            for c in calls
        ],
    )
