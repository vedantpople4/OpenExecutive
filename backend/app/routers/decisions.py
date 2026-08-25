from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.models.decisions import (
    DecisionDetail,
    DecisionListResponse,
    DecisionSummary,
    SubmitDecisionRequest,
    SubmitDecisionResponse,
)
from app.repositories import decisions as repo
from app.services import orchestration

router = APIRouter()


@router.post("/decisions", response_model=SubmitDecisionResponse, status_code=202)
def submit_decision(
    request: SubmitDecisionRequest, background_tasks: BackgroundTasks
) -> SubmitDecisionResponse:
    if request.parent_run_id is not None and repo.get_decision(request.parent_run_id) is None:
        raise HTTPException(status_code=404, detail=f"parentRunId not found: {request.parent_run_id}")

    run_id = repo.create_decision(
        prompt=request.prompt,
        agents=request.agents,
        team_mode_enabled=request.team_mode_enabled,
        parent_run_id=request.parent_run_id,
    )
    background_tasks.add_task(
        orchestration.run_deliberation,
        run_id,
        request.prompt,
        request.agents,
        request.team_mode_enabled,
    )
    return SubmitDecisionResponse(run_id=run_id)


@router.get("/decisions", response_model=DecisionListResponse)
def list_decisions(
    q: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> DecisionListResponse:
    items, next_cursor = repo.list_decisions(q=q, cursor=cursor, limit=limit)
    summaries = [
        DecisionSummary(**repo.to_summary(item, repo.has_children(item["id"]))) for item in items
    ]
    return DecisionListResponse(items=summaries, nextCursor=next_cursor)


@router.get("/decisions/{run_id}", response_model=DecisionDetail)
def get_decision(run_id: str) -> DecisionDetail:
    item = repo.get_decision(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {run_id}")
    return DecisionDetail(**repo.to_detail(item))


@router.post("/decisions/{run_id}/stop")
def stop_decision(run_id: str) -> dict[str, str]:
    # Ordering is load-bearing: signal the worker BEFORE flipping status. The
    # worker picks save_partial_decision vs complete_decision by reading this
    # event, so if the status write landed first and the worker still saw an
    # unset event, it would call complete_decision -- whose terminal guard
    # silently drops the partial results this whole path exists to preserve.
    orchestration.request_cancel(run_id)
    status = repo.stop_decision(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {run_id}")
    return {"status": status}
