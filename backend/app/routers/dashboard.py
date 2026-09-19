from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models.dashboard import RegisterSummary
from app.repositories.decisions import scan_all_decisions
from app.services.dashboard import build_register

router = APIRouter()


@router.get("/dashboard", response_model=RegisterSummary)
def get_dashboard(user_id: str = Depends(get_current_user)) -> RegisterSummary:
    """Scoped to the signed-in user's own decisions -- register-wide meant
    every user's before auth existed, which is exactly the leak fixing this
    endpoint's auth was for."""
    items = scan_all_decisions(user_id)
    return RegisterSummary(**build_register(items))
