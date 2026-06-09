import json
from openexec.ai.prompts import build_deliberation_prompt

core_prompt = "Should we invest in AI infrastructure?"
# Dummy prior outputs structure mimicking expected format
# Round 0: blind reports (empty dict for simplicity)
prior_outputs = {
    0: {},
    1: {
        "ceo": {"summary": "CEO framing summary", "title":"CEO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.8},
        "cfo": {"summary": "CFO analysis", "title":"CFO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.7},
        "cto": {"summary": "CTO analysis", "title":"CTO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.7},
        "cmo": {"summary": "CMO analysis", "title":"CMO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.7},
    },
    2: {
        "cfo": {"summary": "CFO round2", "title":"CFO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.7},
        "cto": {"summary": "CTO round2", "title":"CTO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.7},
    },
    3: {
        "cmo": {"summary": "CMO round3", "title":"CMO", "key_findings":[], "recommendations":[], "risks":[], "alignment_score":0.7},
    }
}

board_summary = """**Consensus**\n- All agree on need for phased PoC.\n**Active Conflicts**\n- CFO vs CTO on timing of spike budget.\n**Key Constraints**\n- CapEx limit $150k until PMF.\n**Current Trajectory**\n- Move toward limited spike budget.\n"""

# Generate prompt for round 4 (CFO agent example)
prompt_r4 = build_deliberation_prompt(
    agent_name="cfo",
    round_num=4,
    core_prompt=core_prompt,
    prior_outputs=prior_outputs,
    challenges={},
    board_summary=board_summary,
)
print("--- Round 4 Prompt (CFO) ---\n")
print(prompt_r4)

# Generate prompt for round 5 (CEO synthesis)
prompt_r5 = build_deliberation_prompt(
    agent_name="ceo",
    round_num=5,
    core_prompt=core_prompt,
    prior_outputs=prior_outputs,
    challenges={},
    board_summary=board_summary,
)
print("\n--- Round 5 Prompt (CEO) ---\n")
print(prompt_r5)
