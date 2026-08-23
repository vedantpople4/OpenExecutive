from fastapi import APIRouter

from app.models.dashboard import RegisterSummary
from app.repositories.decisions import scan_all_decisions
from app.services.dashboard import build_register

router = APIRouter()


@router.get("/dashboard", response_model=RegisterSummary)
def get_dashboard() -> RegisterSummary:
    items = scan_all_decisions()
    return RegisterSummary(**build_register(items))
