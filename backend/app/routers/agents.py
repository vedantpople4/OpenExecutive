"""Static-config endpoints — no database involved, matches Section 3.8-3.10
of the plan. Backed directly by the existing CLI's agent metadata so the two
never drift apart."""

from fastapi import APIRouter, HTTPException

from openexec.agents import TEAM_STRUCTURE
from openexec.agents.templates_ceo import CEOTemplate
from openexec.agents.templates_cfo import CFOTemplate
from openexec.agents.templates_cmo import CMOTemplate
from openexec.agents.templates_cto import CTOTemplate
from openexec.ai.prompts import get_agent_system_prompt

from app.models.agents import Agent, Specialist

router = APIRouter()

_CXO_TEMPLATES = [CEOTemplate, CFOTemplate, CTOTemplate, CMOTemplate]


@router.get("/agents", response_model=list[Agent])
def list_agents() -> list[Agent]:
    return [
        Agent(name=t.name, role=t.role, focus=t.focus, hasSystemPrompt=True)
        for t in _CXO_TEMPLATES
    ]


@router.get("/teams", response_model=dict[str, list[Specialist]])
def get_teams() -> dict[str, list[Specialist]]:
    return {
        cxo: [Specialist(name=name, parentCXO=cxo) for name in specialists]
        for cxo, specialists in TEAM_STRUCTURE.items()
    }


@router.get("/agents/{name}/prompt")
def get_agent_prompt(name: str) -> dict[str, str]:
    try:
        prompt = get_agent_system_prompt(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {name}")
    return {"prompt": prompt}
