from pydantic import BaseModel


class BookingRequest(BaseModel):
    idempotency_key: str
    property_code: str | None = None
    address: str | None = None
    start: str  # ISO 8601 UTC start time
    timezone: str | None = None
    name: str | None = None
    phone: str | None = None
    room_name: str | None = None


class BookingResponse(BaseModel):
    id: int | None = None
    idempotency_key: str
    status: str
    cal_uid: str | None = None
    synced: bool
    address: str | None = None
