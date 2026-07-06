from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from src.models.base_model import BaseModel


class BuyerProfile(BaseModel, table=True):
    """Fast, structured snapshot of a returning buyer, read at call start so the
    assistant recognizes them without waiting on Cognee's graph recall (10-20s, too
    slow for the voice turn). Cognee stays the system of record for deep multi-hop
    recall; this row is the hot cache, written on capture_lead and keyed by phone
    within the realtor's tenant.
    """

    __tablename__ = "buyer_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "phone", name="uq_buyer_profiles_tenant_phone"),
    )

    tenant_id: str = Field(index=True, nullable=False)
    phone: str = Field(index=True, nullable=False)
    name: str | None = Field(default=None)
    budget: str | None = Field(default=None)
    area: str | None = Field(default=None)
    prefs_summary: str | None = Field(default=None)
