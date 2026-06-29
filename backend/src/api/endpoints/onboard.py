from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.memory.store import get_memory_store
from src.schemas.listing_schemas import ConfirmResponse, ListingDraft, OnboardResponse
from src.services.onboard_service import extract_drafts, get_staging_store

router = APIRouter(prefix="/onboard", tags=["onboard"])


@router.post("", response_model=OnboardResponse, status_code=status.HTTP_201_CREATED)
async def onboard(
    realtor: str = Form(...),
    authorized: bool = Form(False),
    file: UploadFile | None = File(None),
) -> OnboardResponse:
    # The realtor must confirm these are their own listings before anything is staged.
    if not authorized:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="confirm you are authorized to use these listings",
        )
    if file is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="provide a listings file"
        )
    drafts = extract_drafts(await file.read(), file.filename)
    if not drafts:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="no listings could be read; try uploading a CSV or PDF instead",
        )
    staged = get_staging_store().stage(realtor, drafts)
    return OnboardResponse(
        realtor=realtor, listings=[ListingDraft(**d) for d in staged]
    )


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm(realtor: str = Form(...)) -> ConfirmResponse:
    # Insert the reviewed staging set into the Cognee memory graph (system of record).
    drafts = get_staging_store().list(realtor)
    if not drafts:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="nothing staged for this realtor"
        )
    await get_memory_store().add_listings({"name": realtor}, drafts)
    get_staging_store().clear(realtor)
    return ConfirmResponse(realtor=realtor, inserted=len(drafts))
