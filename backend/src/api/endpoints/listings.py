from fastapi import APIRouter, HTTPException, status

from src.schemas.listing_schemas import ListingDraft, ListingPatch
from src.services.onboard_service import get_staging_store

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=list[ListingDraft])
async def list_listings(realtor: str) -> list[dict]:
    return get_staging_store().list(realtor)


@router.patch("/{draft_id}", response_model=ListingDraft)
async def patch_listing(draft_id: str, patch: ListingPatch, realtor: str) -> dict:
    updated = get_staging_store().patch(
        realtor, draft_id, patch.model_dump(exclude_unset=True)
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="listing not found")
    return updated


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_listing(draft_id: str, realtor: str) -> None:
    if not get_staging_store().remove(realtor, draft_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="listing not found")
