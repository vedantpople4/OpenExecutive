from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models.compare import CompareResult
from app.repositories import decisions as decisions_repo
from app.services.compare import diff_decisions

router = APIRouter()


@router.get("/compare", response_model=CompareResult)
def compare(old: str, new: str, user_id: str = Depends(get_current_user)) -> CompareResult:
    old_item = decisions_repo.get_owned_decision(old, user_id)
    if old_item is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {old}")

    new_item = decisions_repo.get_owned_decision(new, user_id)
    if new_item is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {new}")

    return CompareResult(**diff_decisions(old_item, new_item))
