"""Response shapes matching frontend/src/api/types.ts exactly (Agent, Specialist)."""

from pydantic import BaseModel, ConfigDict, Field


class Agent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    role: str
    focus: str
    has_system_prompt: bool = Field(alias="hasSystemPrompt")


class Specialist(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    parent_cxo: str = Field(alias="parentCXO")
