from datetime import datetime

from pydantic import BaseModel


class PipelineBooking(BaseModel):
    id: int | None = None
    address: str | None = None
    status: str
    start_utc: datetime | None = None
    phone: str | None = None


class PipelineCall(BaseModel):
    id: int | None = None
    room_name: str
    outcome: str | None = None
    buyer_phone: str | None = None
    ended_at: datetime | None = None


class PipelineResponse(BaseModel):
    bookings: list[PipelineBooking]
    calls: list[PipelineCall]
