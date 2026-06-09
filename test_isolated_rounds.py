import json
from openexec.orchestrator import SimulationState
from openexec.orchestrator_deliberation import DeliberationOrchestrator
from openexec.agents import register_default_agents, registry

# Dummy prior outputs up to round 3 (matching earlier test)
prior_outputs = {
    0: {},
    1: {
        "ceo": {"summary": "CEO framing summary", "title": "CEO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.8},
        "cfo": {"summary": "CFO analysis", "title": "CFO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.7},
        "cto": {"summary": "CTO analysis", "title": "CTO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.7},
        "cmo": {"summary": "CMO analysis", "title": "CMO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.7},
    },
    2: {
        "cfo": {"summary": "CFO round2", "title": "CFO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.7},
        "cto": {"summary": "CTO round2", "title": "CTO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.7},
    },
    3: {
        "cmo": {"summary": "CMO round3", "title": "CMO", "key_findings": [], "recommendations": [], "risks": [], "alignment_score": 0.7},
    }
}

# Board summary to feed into round 4/5
board_summary = """**Consensus**\n- All agree on need for phased PoC.\n**Active Conflicts**\n- CFO vs CTO on timing of spike budget.\n**Key Constraints**\n- CapEx limit $150k until PMF.\n**Current Trajectory**\n- Move toward limited spike budget.\n"""

# Create simulation state
state = SimulationState(
    core_prompt="Should we invest in AI infrastructure?",
    decision_point="Decision required for: Should we invest in AI infrastructure?",
    status="initialized",
)
state.deliberation_outputs = prior_outputs
state.board_summary = board_summary

# Register agents (needed for any internal references)
register_default_agents()

# Instantiate orchestrator
orchestrator = DeliberationOrchestrator(state, registry)

# Initialize AI clients (pre-warm)
orchestrator._init_ai_clients()

# Run round 4 for CFO
cfo_report = orchestrator._call_agent('cfo', 4)
print('--- CFO Round 4 Report ---')
print(json.dumps(cfo_report.__dict__, indent=2))

# Update board summary after round 4 (simulating orchestrator behavior)
orchestrator._update_board_summary(4)
print('\n--- Updated Board Summary after Round 4 ---')
print(state.board_summary)

# Run round 5 CEO synthesis
ceo_report = orchestrator._call_agent('ceo', 5)
print('\n--- CEO Round 5 Report ---')
print(json.dumps(ceo_report.__dict__, indent=2))
