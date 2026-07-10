import json
import sys
from typing import Any, Dict, List
from openexec.ai import AIClient
from openexec.agents.interface import AgentReport
from openexec.agents.templates_ceo import CEOTemplate
from openexec.agents.templates_cfo import CFOTemplate
from openexec.agents.templates_cto import CTOTemplate
from openexec.agents.templates_cmo import CMOTemplate
from openexec.agents.templates_teams import (
    CFOAnalystTemplate, CFOBudgetPlannerTemplate, CFORiskAnalystTemplate,
    CTOEngineeringLeadTemplate, CTOArchitectTemplate, CTOSRETemplate,
    CMOGrowthMarketerTemplate, CMOContentStrategistTemplate, CMOSEOSpecialistTemplate,
    CEOChiefOfStaffTemplate, CEOStrategyAssociateTemplate
)

# Mock SimulationState to avoid dependency on full simulation engine
class MockState:
    def __init__(self, core_prompt: str, data_corpus: Dict[str, str], assumptions: Dict[str, str] = None):
        self.core_prompt = core_prompt
        self.data_corpus = data_corpus
        self.assumptions = assumptions or {}

# Test Cases: "Golden Prompts"
GOLDEN_DATASET = [
    {
        "name": "Infrastructure Pivot",
        "core_prompt": "Should we migrate our core database from PostgreSQL to a specialized Vector DB for AI search capabilities?",
        "data_corpus": {
            "infra_costs.txt": "Current Postgres cost: $500/mo. Vector DB estimated: $2000/mo.",
            "perf_metrics.txt": "Search latency is 200ms. Vector search expected: 20ms."
        },
        "expected_lenses": {
            "cto": ["latency", "architecture", "vector", "feasibility"],
            "cfo": ["cost", "runway", "opex", "budget"],
            "cmo": ["customer", "experience", "competitive"],
            "ceo": ["strategic", "value", "advantage"]
        }
    },
    {
        "name": "Pricing Change",
        "core_prompt": "Should we move from a monthly subscription to a usage-based pricing model?",
        "data_corpus": {
            "usage_logs.txt": "Top 10% of users use 80% of resources.",
            "market_comp.txt": "Competitor X uses usage-based pricing starting at $0.01 per request."
        },
        "expected_lenses": {
            "cfo": ["unit economics", "revenue", "margin", "pricing"],
            "cmo": ["customer segment", "value perception", "pricing power"],
            "cto": ["cost-to-serve", "infrastructure", "scaling"],
            "ceo": ["premium", "long-term", "strategy"]
        }
    }
]

def evaluate_agent(agent, state: MockState, lens_keywords: List[str]) -> Dict[str, Any]:
    try:
        report = agent.analyze(state)

        # 1. Schema Check (already handled by from_llm_response, if it returned we are okay with basic JSON)
        schema_ok = True

        # 2. Lens Check: Does the report contain keywords associated with the role's lens?
        report_text = (report.summary + " " + " ".join(report.key_findings) + " " + " ".join(report.recommendations)).lower()
        lens_found = any(kw.lower() in report_text for kw in lens_keywords)

        # 3. Synthesis Check: Ensure they aren't just dumping the corpus (naive check for long quotes)
        synthesis_ok = True
        for content in state.data_corpus.values():
            if len(content) > 50 and content[:50] in report_text:
                synthesis_ok = False
                break

        return {
            "schema": "✅" if schema_ok else "❌",
            "lens": "✅" if lens_found else "❌",
            "synthesis": "✅" if synthesis_ok else "❌",
            "report": report
        }
    except Exception as e:
        return {
            "schema": "❌",
            "lens": "❌",
            "synthesis": "❌",
            "error": str(e)
        }

def run_eval():
    # Map of all agents to test
    agents_to_test = {
        "ceo": CEOTemplate(),
        "cfo": CFOTemplate(),
        "cto": CTOTemplate(),
        "cmo": CMOTemplate(),
        "financial_analyst": CFOAnalystTemplate(),
        "budget_planner": CFOBudgetPlannerTemplate(),
        "risk_analyst": CFORiskAnalystTemplate(),
        "engineering_lead": CTOEngineeringLeadTemplate(),
        "solutions_architect": CTOArchitectTemplate(),
        "sre": CTOSRETemplate(),
        "growth_marketer": CMOGrowthMarketerTemplate(),
        "content_strategist": CMOContentStrategistTemplate(),
        "seo_specialist": CMOSEOSpecialistTemplate(),
        "chief_of_staff": CEOChiefOfStaffTemplate(),
        "strategy_associate": CEOStrategyAssociateTemplate(),
    }

    # Simplified lens mapping for sub-roles
    sub_role_lenses = {
        "financial_analyst": ["quantitative", "number", "return", "NPV"],
        "budget_planner": ["allocation", "burn", "offset", "budget"],
        "risk_analyst": ["failure", "expected value", "probability", "pre-mortem"],
        "engineering_lead": ["velocity", "bandwidth", "eng-weeks", "critical path"],
        "solutions_architect": ["scale", "moat", "architecture", "bottleneck"],
        "sre": ["blast radius", "reliability", "recovery", "SLA"],
        "growth_marketer": ["LTV", "CAC", "acquisition", "growth loop"],
        "content_strategist": ["narrative", "brand", "trust", "positioning"],
        "seo_specialist": ["search intent", "keyword", "organic", "authority"],
        "chief_of_staff": ["execution", "operational", "alignment", "blocker"],
        "strategy_associate": ["competitive", "benchmark", "leapfrog", "macro"],
    }

    print(f"{'Agent':<25} | {'Schema':<8} | {'Lens':<8} | {'Synth':<8} | Result")
    print("-" * 65)

    for case in GOLDEN_DATASET:
        print(f"\nTest Case: {case['name']}")
        state = MockState(case['core_prompt'], case['data_corpus'])

        for agent_name, agent in agents_to_test.items():
            # Get keywords from the case-specific map if CXO, otherwise from sub_role map
            keywords = case['expected_lenses'].get(agent_name, sub_role_lenses.get(agent_name, []))

            res = evaluate_agent(agent, state, keywords)

            if "error" in res:
                status = f"ERROR: {res['error'][:30]}..."
            else:
                status = "PASS" if (res['schema'] == "✅" and res['lens'] == "✅") else "FAIL"

            print(f"{agent_name:<25} | {res['schema']:<8} | {res['lens']:<8} | {res['synthesis']:<8} | {status}")

if __name__ == "__main__":
    run_eval()
