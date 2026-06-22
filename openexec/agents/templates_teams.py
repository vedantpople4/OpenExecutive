from typing import Any, Dict, Optional
from .interface import AgentReport
from .templates_ceo import CEOTemplate # for base class if needed, but better to use a base template
from openexec.ai.client import AIClient
from openexec.ai.prompts import get_agent_system_prompt

class TeamMemberTemplate:
    """Base template for all sub-role agents."""
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._ai_client = AIClient()

    def analyze(self, state) -> AgentReport:
        """
        Performs specialized narrow-scope research.
        Sub-agents report UPWARD to their CXO.
        """
        from openexec.ai import build_analysis_prompt

        # Use standard analysis prompt builder
        prompt = build_analysis_prompt(
            agent_name=self.agent_name,
            core_prompt=state.core_prompt,
            data_corpus=state.data_corpus,
            assumptions=state.assumptions
        )

        system_prompt = get_agent_system_prompt(self.agent_name)

        # Call LLM
        raw_response = self._ai_client.complete_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )

        # Use standard report factory
        from .interface import AgentReport
        return AgentReport.from_llm_response(self.agent_name, raw_response)

# Specific Sub-Roles
class CFOAnalystTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("financial_analyst")

class CFOBudgetPlannerTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("budget_planner")

class CFORiskAnalystTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("risk_analyst")

class CTOEngineeringLeadTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("engineering_lead")

class CTOArchitectTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("solutions_architect")

class CTOSRETemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("sre")

class CMOGrowthMarketerTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("growth_marketer")

class CMOContentStrategistTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("content_strategist")

class CMOSEOSpecialistTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("seo_specialist")

class CEOChiefOfStaffTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("chief_of_staff")

class CEOStrategyAssociateTemplate(TeamMemberTemplate):
    def __init__(self):
        super().__init__("strategy_associate")
