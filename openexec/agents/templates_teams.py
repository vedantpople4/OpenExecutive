from .interface import AgentReport
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
            assumptions=state.assumptions,
            research_cfg=getattr(state, 'research_cfg', None),
            past_decisions_context=getattr(state, 'past_decisions_context', '') or None,
        )

        system_prompt = get_agent_system_prompt(self.agent_name)

        # Call LLM with retry; fall back to a stub on total failure so one
        # specialist error can't abort the whole --teams run.
        try:
            raw_response = self._ai_client.complete_json_with_retry(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            return AgentReport.from_llm_response(self.agent_name, raw_response)
        except Exception as e:
            print(f"  [WARN] {self.agent_name} analysis failed: {e}. Using fallback stub.")
            return AgentReport(
                title=f"{self.agent_name.upper()} Analysis (Fallback)",
                summary=f"Specialist analysis could not be generated for {self.agent_name}.",
                round_number=0,
                alignment_score=0.5,
                is_fallback=True,
            )

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
