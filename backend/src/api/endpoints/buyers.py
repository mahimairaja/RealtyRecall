import logging
from typing import Any

from fastapi import APIRouter, status

from src.core.clerk import CurrentTenant
from src.core.tenant import AgentTenant
from src.memory.store import get_memory_store
from src.repository import buyer_profile_repository
from src.schemas.buyer_schemas import (
    BuyerForgetResponse,
    BuyerProfileResponse,
    BuyerRecall,
    BuyerSummary,
    BuyerUpsert,
    BuyerUpsertResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buyers", tags=["buyers"])


def _summarize_criteria(criteria: dict[str, Any]) -> str:
    """A short human phrase of a buyer's stated criteria for the fast profile, e.g.
    "3+ beds, under $480,000 in Sarnia"."""
    parts: list[str] = []
    beds = criteria.get("minBeds")
    if beds:
        parts.append(f"{beds}+ beds")
    price = criteria.get("maxPrice")
    if price:
        try:
            parts.append(f"under ${int(price):,}")
        except (TypeError, ValueError):
            pass
    area = criteria.get("area")
    if area:
        parts.append(f"in {area}")
    return ", ".join(parts)


# The realtor's dashboard list of remembered buyers. Console-authed (Clerk org), unlike the
# per-buyer agent routes below which the assistant calls mid-call behind the agent secret.
@router.get("", response_model=list[BuyerSummary])
async def list_buyers(tenant_id: CurrentTenant) -> list[dict]:
    return await get_memory_store().list_buyers(tenant_id)


@router.post(
    "", response_model=BuyerUpsertResponse, status_code=status.HTTP_201_CREATED
)
async def upsert_buyer(
    payload: BuyerUpsert,
    tenant_id: AgentTenant,
) -> BuyerUpsertResponse:
    # Buyers are keyed by phone within the realtor's tenant and owned by Cognee (a per-buyer,
    # per-tenant dataset). Upsert is safe to call repeatedly: a return call updates memory.
    await get_memory_store().upsert_buyer(tenant_id, payload.model_dump())
    # Dual-write a fast structured snapshot so the next call recognizes this buyer
    # instantly (get_buyer_profile reads the row, not Cognee). Best-effort: a failure
    # here must not lose the lead, which Cognee already persisted above.
    if payload.phone:
        criteria = payload.criteria or {}
        try:
            await buyer_profile_repository.upsert(
                tenant_id,
                payload.phone,
                name=payload.name,
                area=criteria.get("area"),
                budget=str(criteria["maxPrice"]) if criteria.get("maxPrice") else None,
                prefs_summary=_summarize_criteria(criteria) or None,
            )
        except Exception:  # noqa: BLE001  (fast cache is best-effort)
            logger.warning("buyer_profile fast upsert failed", exc_info=True)
    return BuyerUpsertResponse(phone=payload.phone, name=payload.name)


@router.get("/{phone}/profile", response_model=BuyerProfileResponse)
async def get_buyer_profile(
    phone: str,
    tenant_id: AgentTenant,
) -> BuyerProfileResponse:
    # The FAST recall path: a direct row read the assistant does at call start, so a
    # returning buyer is recognized in a normal voice turn instead of waiting on the
    # 10-20s Cognee graph recall. found=false means a new or forgotten caller.
    profile = await buyer_profile_repository.get(tenant_id, phone)
    if profile is None:
        return BuyerProfileResponse(found=False, phone=phone)
    return BuyerProfileResponse(
        found=True,
        phone=phone,
        name=profile.name,
        budget=profile.budget,
        area=profile.area,
        prefs_summary=profile.prefs_summary,
    )


@router.get("/{phone}", response_model=BuyerRecall)
async def get_buyer(
    phone: str,
    tenant_id: AgentTenant,
) -> BuyerRecall:
    # On call start the assistant looks up the caller by phone within this realtor's tenant.
    # Always 200; found=false means a new (or forgotten) buyer, so the agent opens fresh.
    store = get_memory_store()
    result = await store.get_buyer(tenant_id, phone)
    if result.get("found") and result.get("summary"):
        result["nearby"] = await store.recall_nearby(tenant_id, str(result["summary"]))
    return BuyerRecall(**result)


# Destructive, so it requires the agent secret (AgentTenant) and only ever removes a buyer
# within the asserting realtor's tenant. The agent calls this with its verified caller phone
# (forget_me derives it, never an argument). POST-M0: also require proof of possession of the
# phone (an OTP / signed token) before deletion.
@router.delete("/{phone}", response_model=BuyerForgetResponse)
async def forget_buyer(
    phone: str,
    tenant_id: AgentTenant,
) -> BuyerForgetResponse:
    # Forget on request: remove exactly this buyer's per-tenant Cognee dataset. A later call
    # from this phone is then treated as a brand-new buyer with no history.
    await get_memory_store().forget_buyer(tenant_id, phone)
    return BuyerForgetResponse(forgotten=True, phone=phone)
