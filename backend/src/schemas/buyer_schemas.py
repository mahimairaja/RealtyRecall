from typing import Any

from pydantic import BaseModel


class BuyerUpsert(BaseModel):
    phone: str
    name: str | None = None
    email: str | None = None
    criteria: dict[str, Any] | None = None
    room_name: str | None = None


class BuyerUpsertResponse(BaseModel):
    phone: str
    name: str | None = None


class BuyerForgetResponse(BaseModel):
    forgotten: bool
    phone: str


class BuyerRecall(BaseModel):
    found: bool
    phone: str
    summary: str | None = None
    nearby: str | None = None


class BuyerProfileResponse(BaseModel):
    """The fast structured profile read at call start (not Cognee). found=false is a
    new or forgotten caller."""

    found: bool
    phone: str
    name: str | None = None
    budget: str | None = None
    area: str | None = None
    prefs_summary: str | None = None


class BuyerSummary(BaseModel):
    """A remembered buyer listed on the realtor's dashboard."""

    phone: str | None = None
    name: str | None = None
    email: str | None = None
    criteria: dict[str, Any] | None = None
