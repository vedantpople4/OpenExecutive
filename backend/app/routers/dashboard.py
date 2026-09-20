from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models.dashboard import RegisterSummary
from app.repositories.decisions import list_decisions_for_user
from app.services.dashboard import build_register

router = APIRouter()


@router.get("/dashboard", response_model=RegisterSummary)
def get_dashboard(user_id: str = Depends(get_current_user)) -> RegisterSummary:
    items = list_decisions_for_user(user_id)
    return RegisterSummary(**build_register(items))
