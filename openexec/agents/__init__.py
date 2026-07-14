# Executive Board Agents Package
"""Agent registry and base classes."""

from typing import Protocol, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .interface import AgentProtocol


class AgentRegistry:
    """Registry for managing executive agent instances."""

    def __init__(self):
        self._agents: dict[str, "AgentProtocol"] = {}
        self._classes: dict[str, Type["AgentProtocol"]] = {}

    def register(self, agent_class: Type["AgentProtocol"], name: str | None = None) -> None:
        """Register an agent class."""
        key = name or agent_class.__name__
        self._classes[key] = agent_class

    def unregister(self, name: str) -> bool:
        """Unregister an agent by name. Returns True if successful."""
        if name in self._agents:
            del self._agents[name]
        if name in self._classes:
            del self._classes[name]
        return True

    def get(self, name: str) -> "AgentProtocol | None":
        """Get an agent instance by name, creating one if needed."""
        if name not in self._agents and name in self._classes:
            self._agents[name] = self._classes[name]()
        return self._agents.get(name)

    def get_class(self, name: str) -> Type["AgentProtocol"] | None:
        """Get a registered agent class by name."""
        return self._classes.get(name)

    def list_names(self) -> list[str]:
        """Return all registered agent names."""
        return list(self._classes.keys())


registry = AgentRegistry()


TEAM_STRUCTURE = {
    "cfo": ["financial_analyst", "budget_planner", "risk_analyst"],
    "cto": ["engineering_lead", "solutions_architect", "sre"],
    "cmo": ["growth_marketer", "content_strategist", "seo_specialist"],
    "ceo": ["chief_of_staff", "strategy_associate"],
}

def register_default_agents() -> None:
    """Register all default executive agents."""
    from .templates_ceo import CEOTemplate
    from .templates_cfo import CFOTemplate
    from .templates_cto import CTOTemplate
    from .templates_cmo import CMOTemplate
    from .templates_teams import (
        CFOAnalystTemplate, CFOBudgetPlannerTemplate, CFORiskAnalystTemplate,
        CTOEngineeringLeadTemplate, CTOArchitectTemplate, CTOSRETemplate,
        CMOGrowthMarketerTemplate, CMOContentStrategistTemplate, CMOSEOSpecialistTemplate,
        CEOChiefOfStaffTemplate, CEOStrategyAssociateTemplate
    )

    registry.register(CEOTemplate, "ceo")
    registry.register(CFOTemplate, "cfo")
    registry.register(CTOTemplate, "cto")
    registry.register(CMOTemplate, "cmo")

    # Register sub-roles
    registry.register(CFOAnalystTemplate, "financial_analyst")
    registry.register(CFOBudgetPlannerTemplate, "budget_planner")
    registry.register(CFORiskAnalystTemplate, "risk_analyst")
    registry.register(CTOEngineeringLeadTemplate, "engineering_lead")
    registry.register(CTOArchitectTemplate, "solutions_architect")
    registry.register(CTOSRETemplate, "sre")
    registry.register(CMOGrowthMarketerTemplate, "growth_marketer")
    registry.register(CMOContentStrategistTemplate, "content_strategist")
    registry.register(CMOSEOSpecialistTemplate, "seo_specialist")
    registry.register(CEOChiefOfStaffTemplate, "chief_of_staff")
    registry.register(CEOStrategyAssociateTemplate, "strategy_associate")


# Default agents (will be implemented later)
DEFAULT_AGENTS = [
    "ceo",      # Chief Executive Officer
    "cfo",      # Chief Financial Officer
    "cto",      # Chief Technology Officer
    "cmo",      # Chief Marketing Officer
]
