"""Matches frontend/src/api/types.ts's RegisterSummary exactly."""

from pydantic import BaseModel


class TopRisk(BaseModel):
    text: str
    count: int


class AgentAlignmentStat(BaseModel):
    mean: float
    samples: int


class MonthCount(BaseModel):
    month: str
    count: int


class RegisterSummary(BaseModel):
    total_decisions: int
    distinct_prompts: int
    total_action_items: int
    high_priority_actions: int
    top_risks: list[TopRisk]
    agent_alignment: dict[str, AgentAlignmentStat]
    per_month: list[MonthCount]
    most_recent: str
