"""Response/request shapes matching frontend/src/api/types.ts's DecisionSummary
and DecisionDetail exactly (Section 3.1-3.3 of the plan). agent_reports and
deliberation_rounds stay loosely typed (dict) here — nothing populates them
with real content until the deferred LLM-orchestration phase writes them."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActionItem(BaseModel):
    priority: str
    task: str
    owner: str
    due_date: str


class BoardDecision(BaseModel):
    consensus_points: list[str] = Field(default_factory=list)
    dissent_points: list[str] = Field(default_factory=list)
    final_priority_actions: list[str] = Field(default_factory=list)
    dissenting_opinions: list[str] = Field(default_factory=list)
    contingencies: list[str] = Field(default_factory=list)
    summary: str | None = None
    status: str | None = None


class DecisionSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
    timestamp: str
    prompt: str
    decision_point: str | None = Field(default=None, alias="decisionPoint")
    executive_summary: str | None = Field(default=None, alias="executiveSummary")
    action_item_count: int = Field(alias="actionItemCount")
    top_risks: list[str] = Field(alias="topRisks")
    agent_alignment: dict[str, float] = Field(alias="agentAlignment")
    parent_run_id: str | None = Field(default=None, alias="parentRunId")
    has_children: bool | None = Field(default=None, alias="hasChildren")
    status: str | None = None


class DecisionListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[DecisionSummary]
    next_cursor: str | None = Field(alias="nextCursor")


class DecisionDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
    timestamp: str
    prompt: str
    decision_point: str | None
    executive_summary: str
    parent_run_id: str | None = Field(default=None, alias="parentRunId")
    agent_reports: dict[str, Any] = Field(default_factory=dict)
    deliberation_rounds: dict[str, Any] = Field(default_factory=dict)
    board_decision: BoardDecision
    action_items: list[ActionItem] = Field(default_factory=list)
    overall_risk_assessment: list[str] = Field(default_factory=list)
    synthesized_recommendations: list[str] = Field(default_factory=list)
    fallback_warnings: list[str] = Field(default_factory=list)
    status: str | None = None
    error_message: str | None = None


class SubmitDecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str
    agents: list[str]
    team_mode_enabled: bool = Field(alias="teamModeEnabled")
    parent_run_id: str | None = Field(default=None, alias="parentRunId")


class SubmitDecisionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
