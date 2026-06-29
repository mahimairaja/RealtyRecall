from fastapi import APIRouter, Depends, status

from src.core.widget_guard import enforce_widget_guard
from src.schemas.booking_schemas import BookingRequest, BookingResponse
from src.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingRequest,
    _: None = Depends(enforce_widget_guard),
) -> BookingResponse:
    result = await booking_service.book_showing(payload.model_dump())
    return BookingResponse(**result)
