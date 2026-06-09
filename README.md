# OpenExec — Executive Board Simulation

> Your AI-powered executive board meeting. Four specialized AI agents debate your business decision through a real multi-round deliberation, then deliver a synthesized board decision with explicit consensus, dissent, and committed action items.

## TL;DR

```bash
openexec run "Buy vs lease equipment?"
```

Get back a structured board report with: a CEO board decision, a 5-round deliberation transcript showing how executives challenged and revised each other, individual analyses from CEO/CFO/CTO/CMO, prioritized action items, and quantified risks.

## What Problem Does It Solve?

The board simulation originally hit context over‑flows in later rounds, causing fallback stubs. The new flow adds a **Scribe** summarizer and a `board_summary` field in `SimulationState`. After each delegation round (≥ 2) the orchestrator calls the Scribe to distill consensus, conflicts, constraints, and trajectory into a concise markdown summary. Subsequent round prompts include this summary plus only the immediate prior round’s reports, keeping the LLM context lean while preserving decision history. This eliminates fallback usage and produces full, substantive reports for Rounds 3‑5.

## New Flow Overview

1. **SimulationState** now holds `board_summary: str`.
2. **DeliberationOrchestrator.run_deliberation** updates `board_summary` after each round via `_update_board_summary`.
3. **build_deliberation_prompt** receives `board_summary` and injects it into prompts for rounds 3‑5.
4. **_call_agent** uses the lean context (summary + prior round) and falls back only as last resort.
5. **Scribe** (`SCRIBE_SYSTEM_PROMPT`) generates a JSON `{"board_summary": "..."}` with four sections: Consensus, Active Conflicts, Key Constraints, Current Trajectory.

## How to Use

Run the simulation as before:

```bash
openexec run "Should we invest in AI infrastructure?"
```

The generated `board_report.md` now contains full detailed reports for all rounds, no fallback stubs.

## Implementation Files

- `openexec/orchestrator_deliberation.py` – added `_update_board_summary`, lean context handling.
- `openexec/ai/prompts.py` – added `SCRIBE_SYSTEM_PROMPT` and updated `build_deliberation_prompt` signature.
- `openexec/orchestrator.py` – added `board_summary` field to `SimulationState`.
- `README.md` – updated with new flow description.


Business decisions get made by one person thinking in one direction. OpenExec forces structured disagreement from four distinct perspectives — and makes those perspectives *talk to each other* until a real decision emerges. It's not four parallel monologues. It's an actual board meeting where positions evolve under pressure.

## Setup

**Prerequisites**

- Python 3.10+
- Ollama running locally (`ollama serve`)

**Install**

```bash
# Via pip
pip install -e .

# Or clone manually
git clone <repo-url>
cd OpenExec
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

**Configure the AI provider**

```bash
openexec setup
```

Creates `settings.json` with defaults. Models tested: `google/gemma-4-e2b`, `llama3`. Any OpenAI-compatible Ollama model works.

**Company data (optional)**

Drop files into `data/` — they get auto-loaded into every agent's analysis:

```
data/
├── company_background.md
├── team_structure.md
└── case_studies.md
```

## Usage

### Basic

```bash
openexec run "Should we buy or lease new equipment?"
```

Produces `board_report.md`, exports action items, and logs the decision.

### Counterfactual Analysis

```bash
# Assume market growth is 2%
openexec run "Should we expand to Europe?" --assume market_growth=2%

# Multiple assumptions
openexec run "Build new server?" --assume budget=100k --assume competitor_exists=false
```

### Multi-Objective Optimization

```bash
# Weighted agent priorities
openexec run "Build vs buy?" --weight cfo=0.5 --weight cto=0.3
openexec run "Migrate to Kubernetes?" --weight cto=0.6 --weight cfo=0.4
```

### Full Command Reference

```bash
openexec run "Question"                          # Basic run
openexec run "Q" -o report.md                      # Custom output
openexec run "Q" -s summary.md                     # With executive summary
openexec run "Q" -e csv                            # Export action items (json/csv/checklist)
openexec run "Q" -d ./company_data                 # Custom data directory
openexec run "Q" --no-memory                       # Disable memory context
openexec run "Q" --assume k=v --assume k2=v2       # Counterfactual analysis
openexec run "Q" --weight cfo=0.5 --weight cto=0.3 # Weighted agent priorities
```

### Other Commands

```bash
openexec history                 # List past decisions
openexec search "GPU investment"  # Search memory
openexec performance              # Agent rating metrics
openexec kb ingest doc.pdf finance  # Add to knowledge base
openexec kb list                  # List KB documents
openexec kb search "market timing" # Search KB
openexec batch prompts.txt        # Run multiple simulations
```

## Output Structure

A `board_report.md` looks like this:

```markdown
# Executive Board Simulation Report

## Executive Summary
[One-line overview]

## Board Decision
[One-paragraph statement of board position]

### Consensus Points
- [Specific agreement across all four execs]

### Final Priority Actions
- [Action] | Owner: CTO | Timeframe: 2 Weeks

### Dissenting Points
- CFO: [disagreement]
- CTO: [disagreement]

### Contingencies
- If [condition], then [revisit or change action]

## Deliberation Transcript
### Round 1
**CEO**: [frames the board, names 3 conflicts, directs questions]

### Round 2
**CFO**: [responds, agrees/conflicts with CTO]
**CTO**: [responds, agrees/conflicts with CFO]

### Round 3
**CMO**: [responds, raises market challenges]

### Round 4
**CFO**: [revised recommendation + what changed]
**CTO**: [revised recommendation + what changed]
**CMO**: [revised recommendation + what changed]

### Round 5
**CEO**: [synthesizes — the board decision]

## Individual Agent Reports
[CEO/CFO/CTO/CMO: title, summary, key findings, recommendations, risks]

## Action Items
- [HIGH/MEDIUM/LOW] [Task] | Owner: CFO | Due: TBD

## Overall Risk Assessment
- [CEO] [risk description]

## Risk Quantification
[Probability × Impact matrix + scored risks]
```

## Tech Stack

| Layer           | Technology | Role |
|-----------------|-----------|------|
| **Runtime**     | Python 3.10+ | Core language |
| **CLI**         | Typer (`typer`) | CLI with rich formatting |
| **LLM Backend** | Ollama        | Local AI inference |
| **Parsers**     | `json5`       | Relaxed JSON parsing |
| **Config**      | `python-dotenv`, `pyyaml` | Settings and env management |
| **Dev**         | `pytest`, `black`, `ruff` | Testing and linting |
| **Progress**    | `tqdm`        | Progress bars |

### 4-Layer JSON Robustness Pipeline

The LLM client uses a 4-layer pipeline to handle malformed JSON output:

1. **Preprocess** — Strip markdown fences, bracket-matching, remove BOM/\x00
2. **Structural fixes** — Fix trailing commas, unescaped `\n`/`\r`, unquoted keys
3. **json5 fallback** — Use `json5.loads()` for relaxed JSON parsing
4. **Self-correction** — Re-call LLM with a correction prompt if all layers fail

## Security

All user prompts are sanitized before processing to mitigate prompt injection attacks via `sanitize_prompt()` in `src/utils.py`:

- Removes null bytes and control characters
- Filters common injection patterns (`ignore instructions`, `new instructions:`, etc.)
- Strips markdown image links that could inject context
- Normalizes whitespace

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Setup AI provider
openexec setup

# 3. Run your first simulation
openexec run "Should we invest in AI infrastructure?"

# 4. Check the decision log
openexec history
```
