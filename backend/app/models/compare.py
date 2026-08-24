"""Matches frontend/src/api/types.ts's CompareResult/AgentScoreDelta exactly
(already snake_case throughout — no aliasing needed)."""

from pydantic import BaseModel


class AgentScoreDelta(BaseModel):
    agent: str
    old: float | None
    new: float | None
    delta: float | None


class CompareResult(BaseModel):
    old_prompt: str
    new_prompt: str
    same_prompt: bool
    old_summary: str
    new_summary: str
    consensus_added: list[str]
    consensus_removed: list[str]
    dissent_added: list[str]
    dissent_removed: list[str]
    actions_added: list[str]
    actions_removed: list[str]
    risks_added: list[str]
    risks_removed: list[str]
    agent_scores: list[AgentScoreDelta]
