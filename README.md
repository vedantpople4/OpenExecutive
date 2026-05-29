# OpenExec — Executive Board Simulation System

> Your AI-powered executive board meeting. Four specialized AI agents debate your business decision, revise positions through a real multi-round deliberation, and deliver a synthesized board decision with explicit consensus, dissent, and committed action items.

---

## TL;DR

Give OpenExec a business question:

```bash
openexec run "Buy vs lease equipment?"
```

Get back a structured board report with: a CEO board decision, a 5-round deliberation transcript showing how executives challenged and revised each other, individual analyses from CEO/CFO/CTO/CMO, prioritized action items, and quantified risks.

---

## What Problem Does It Solve?

Business decisions get made by one person thinking in one direction. OpenExec forces structured disagreement from four distinct perspectives — and makes those perspectives *talk to each other* until a real decision emerges. It's not four parallel monologues. It's an actual board meeting where positions evolve under pressure.

If you run the same decision through OpenExec twice for the same question vs a competitor, you don't get a generic list of pros and cons — you get an explicit board decision that names who agrees, who disagrees, what changed their mind, and what happens if conditions change.

---

## 🎯 Project Summary

**OpenExec** is a multi-agent simulation framework where four AI "executives" (CEO, CFO, CTO, CMO) independently analyze a business decision, then enter a structured multi-round deliberation that mirrors a real board meeting. Each agent sees the others' work, challenges it, revises their own position, and the CEO produces a final board decision.

### The Core Difference: Real Deliberation vs Parallel Analysis

Traditional multi-agent systems run each agent independently and concatenate the results. OpenExec runs an actual 5-round deliberation loop:

| Round | Who Speaks | What Happens |
|-------|-----------|--------------|
| 1 | CEO | Frames the board. Names top 3 conflicts. Directs questions at CFO/CTO/CMO. |
| 2 | CFO + CTO | Respond to CEO's questions. Cross-reference each other's position for agreements and conflicts. |
| 3 | CMO | Reads all prior rounds. Raises market-side challenges back at CFO and CTO. |
| 4 | CFO + CTO + CMO | Revise their positions based on challenges received. Confirms or updates recommendations. |
| 5 | CEO | Synthesizes all rounds into a **board decision** with consensus points, dissent points, final priority actions, and contingencies. |

The output isn't a stack of reports — it's a decision with accountability assigned to it.

---

## 🧠 Ideology & Design Philosophy

**"Dissent is a feature, not a bug."**

Most AI business tools are built to be agreeable — they tell you what you want to hear. OpenExec is built around productive conflict. The goal is to surface *the real disagreement* between financial prudence and technical ambition, between market timing and operational capacity. The board decision is better when CFO's skepticism forced CTO to defend their recommendation, and when CMO's customer data made CFO revise their cost model.

**"Simulate the meeting, not the report."**

The report is a byproduct of the meeting. OpenExec's architecture is designed around the deliberation process first. Phase 1-2 generate the raw analysis. Phase 3 is the actual product — it transforms independent monologues into a synthesized decision.

**"Be honest about uncertainty."** Every agent has an `alignment_score` (0.0-1.0). In OpenExec, 0.5 is a valid score when data is thin. Agents are explicitly told: do not inflate your confidence.

**"Context compounds over time."**

OpenExec remembers every decision it has ever made. New simulations inject past decisions as context. The longer you use it, the more history it has to reason from — including patterns in what was decided, what was implemented, and what the outcome was (if you provide feedback).

---

## 🏗️ Architecture

```
User prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  cli.py                                                  │
│  Typer-based CLI. Validates settings, runs orchestrator.│
│  Supports: --assume (counterfactual), --weight (optim) │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  orchestrator.py — Orchestrator                         │
│  Runs 4 phases in sequence. Holds SimulationState.      │
│  - Phase 1: Inception (CEO sets the stage)             │
│  - Phase 2: Analysis (CFO/CTO/CMO work alone)           │
│  - Phase 3: Deliberation (DeliberationOrchestrator)    │
│  - Phase 4: Synthesis (compile final report)            │
│  Emits events to EventStore for auditability           │
└───────────────────────────┬─────────────────────────────┘
                            │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────────┐
│ DeliberationOrchestrator │       │ agent_outputs (Phase 2) │
│ (orchestrator_deliberation.py)   │ CEO/CFO/CTO/CMO reports │
│ Runs 5-round board loop.        │ stored as AgentReport   │
│ Calls build_deliberation_prompt  │ objects                 │
│ for each round.                  └──────────────────────────┘
└────────────┬──────────────┘
              │
     ┌────────┴─────────┐
     │ 4 template agents│
     │ ceo/cfo/cto/cmo  │
     │ (agents/templates_*.py)│
     └────────┬─────────┘
              │        ┌──────────────────────┐
              └───────►│ prompts.py           │
                       │ - AGENT_SYSTEM_PROMPTS│
                       │ - DELIBERATION_MODIFIERS│
                       │ - build_deliberation_prompt()
                       │ - build_analysis_prompt() │
                       └───────────────────────┘
                                          │
                                ┌─────────▼──────────────┐
                                │  ai/client.py           │
                                │  Delegates to provider  │
                                │  4-layer JSON pipeline  │
                                └─────────┬──────────────┘
                                          │
                                ┌─────────▼──────────────┐
                                │ BaseProvider Interface  │
                                │ (abstract_provider.py) │
                                └─────────┬──────────────┘
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                 ▼
              ┌──────────────────────┐        ┌──────────────────────────┐
              │ OllamaProvider       │        │ Future: OpenAIProvider   │
              │ (ollama_provider.py) │        │ (not yet implemented)    │
              │ Local Ollama API     │        └──────────────────────────┘
              └──────────────────────┘

Event Sourcing Layer:
┌─────────────────────────────────────────────────────────┐
│  events.py — Event type definitions                    │
│  event_store.py — Append-only event persistence        │
│  Events: simulation_initialized, agent_report_generated │
│  deliberation_round_completed, synthesis_completed, etc │
└─────────────────────────────────────────────────────────┘
```

### Key Files

| File | Role |
|------|------|
| `src/cli.py` | CLI entry point via Typer. Config loading, simulation runner, all subcommands. Supports `--assume` and `--weight` flags. |
| `src/orchestrator.py` | Orchestrator class. Manages SimulationState. Runs Phase 1-4 pipeline. Emits events to EventStore. |
| `src/orchestrator_deliberation.py` | `DeliberationOrchestrator` class. Runs the 5-round board meeting. |
| `src/ai/abstract_provider.py` | `BaseProvider` abstract class defining the LLM provider interface. |
| `src/ai/ollama_provider.py` | `OllamaProvider` implementation for local Ollama API. Includes 4-layer JSON parsing pipeline. |
| `src/ai/client.py` | `AIClient`. Delegates to BaseProvider. Owns 4-layer JSON robustness pipeline as fallback. |
| `src/ai/prompts.py` | All prompt engineering: agent personas, decision routing, deliberation prompts. `build_analysis_prompt()` supports counterfactual assumptions. |
| `src/agents/interface.py` | `AgentReport` dataclass — every field any agent can return. |
| `src/agents/templates_ceo.py` | CEO persona, AI analysis, deliberation invocation. |
| `src/agents/templates_cfo.py` | CFO persona, financial analysis, AI invocation. |
| `src/agents/templates_cto.py` | CTO persona, technical analysis, AI invocation. |
| `src/agents/templates_cmo.py` | CMO persona, market analysis, AI invocation. |
| `src/main.py` | `write_report()` — renders the final markdown. Injects board decision + deliberation transcript. |
| `src/events.py` | Event type definitions for event sourcing (SimulationInitialized, AgentReportGenerated, DeliberationRoundCompleted, etc.). |
| `src/event_store.py` | `EventStore` class for event persistence, state reconstruction, and event replay. |
| `src/decision_tracker.py` | Logs every decision to `decisions/decision_YYYYMMDD_HHMMSS.json`. |
| `src/memory.py` | Multi-session persistent memory. Injects past decisions as context for new simulations. |
| `src/feedback.py` | Feedback system. Records agent recommendation ratings and tracks outcomes over time. |
| `src/knowledge_base.py` | RAG-style document ingestion. Lets you feed the system your own PDFs and docs. |
| `src/risk_analyzer.py` | Scans agent risks, scores them (probability × impact), generates visual risk matrix. |
| `src/export.py` | Multi-format export: JSON, CSV, Markdown checklist from extracted action items. |
| `src/utils.py` | Utility functions including `sanitize_prompt()` for prompt injection defense. |

---

## ⚙️ Setup

### Prerequisites

- **Python 3.10+**
- **Ollama** running locally (`ollama serve`)

### 1. Clone & Virtual Environment

```bash
git clone <repo-url>
cd OpenExec
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure the AI Provider

Create `settings.json` in the project root:

```json
{
  "ai": {
    "base_url": "http://localhost:11434/v1",
    "model": "google/gemma-4-e2b",
    "temperature": 0.7,
    "max_tokens": 4096,
    "provider": "openai_compatible",
    "timeout": 120
  },
  "agents": {
    "enabled": ["ceo", "cfo", "cto", "cmo"],
    "analysis_depth": "medium",
    "confidence_threshold": 0.6,
    "max_interactions": 10
  },
  "simulation": {
    "phases": [
      {"name": "inception", "weight": 0.1},
      {"name": "analysis", "weight": 0.5},
      {"name": "review", "weight": 0.25},
      {"name": "synthesis", "weight": 0.1}
    ]
  }
}
```

> **Models tested:** `google/gemma-4-e2b` (fast), `llama3` (balanced). Any OpenAI-compatible Ollama model works. The deliberation prompts are ~1200 tokens — make sure your model context window is ≥ 4096 tokens.

### 3. Company Data (Optional but Recommended)

Drop files into the `data/` directory. They get automatically loaded and fed into every agent's analysis:

```
data/
├── company_background.md   # Overview, mission, product
├── team_structure.md        # Org, roles, capacity
└── case_studies.md          # Reference decisions and outcomes
```

---

## 🚀 Usage

### First Simulation

```bash
openexec run "Should we buy or lease new equipment?"
```

This runs the full pipeline and produces `board_report.md`, action item exports, and logs the decision.

### Counterfactual Analysis

Run simulations with hypothetical conditions:

```bash
# Assume market growth is 2%
openexec run "Should we expand to Europe?" --assume market_growth=2%

# Multiple assumptions
openexec run "Build new server?" --assume budget=100k --assume competitor_exists=false

# Combined with other options
openexec run "Buy vs lease equipment?" -o report.md --assume market_growth=3%
```

### Multi-Objective Optimization

Weight agent recommendations by priority:

```bash
# CFO's recommendations weighted 50%, CTO's 30%
openexec run "Build vs buy?" --weight cfo=0.5 --weight cto=0.3

# Higher CTO priority for technical decisions
openexec run "Migrate to Kubernetes?" --weight cto=0.6 --weight cfo=0.4

# Combined with counterfactual assumptions
openexec run "Series A now?" --assume runway=18mo --weight ceo=0.4 --weight cfo=0.3 --weight cto=0.3
```

### Full Command Reference

```bash
# Basic
openexec run "Should we expand to European markets?"

# Custom output
openexec run "Hire more engineers?" -o report.md

# With executive summary
openexec run "Series A now or wait?" -s summary.md

# Export action items
openexec run "Buy vs lease equipment?" -e csv   # or json, checklist

# Custom data directory
openexec run "Build vs buy?" -d ./company_data

# Disable memory context
openexec run "New decision" --no-memory

# Counterfactual analysis (what-if scenarios)
openexec run "Should we expand?" --assume market_growth=2% --assume competitor_exists=false

# Multi-objective optimization (weighted agent priorities)
openexec run "Build new infrastructure?" --weight cto=0.6 --weight cfo=0.4

# Combined flags
openexec run "GPU investment?" --assume budget=500k --weight cfo=0.5 --weight cto=0.5 -o gpu_report.md
```

### Other Commands

```bash
openexec history                 # List past decisions
openexec search "GPU investment"  # Search memory
openexec performance              # Agent rating metrics
openexec kb ingest doc.pdf finance  # Add to knowledge base
openexec kb list                  # List KB documents
openexec kb search "market timing"  # Search KB
openexec batch prompts.txt        # Run multiple simulations
```

---

## 📊 Workflow: What Happens Inside

### Phase 1 — Inception (CEO)

CEO reads the prompt and sets the strategic frame: *"Here is what we're deciding, here is the core tension, here is what matters most."*

### Phase 2 — Analysis (CFO, CTO, CMO)

Each works alone, blind to the others. They return structured reports:

```python
@dataclass
class AgentReport:
    title: str
    summary: str
    key_findings: list[str]
    recommendations: list[str]
    risks: list[str]
    alignment_score: float          # 0.0–1.0, be honest

    # Role-specific fields
    verdict: str                    # CEO: strategic, CFO: financial, etc.

    # CFO-specific
    capex_vs_opex: str
    runway_impact_6mo: str
    series_a_signal: str

    # CTO-specific
    technical_verdict: str          # Green / Yellow / Red
    build_cost_order_of_magnitude: str
    moat_impact: str

    # CMO-specific
    market_verdict: str
    pricing_impact: str
    customer_segment_view: str

    # Deliberation fields
    agreements: list[str]
    conflicts: list[str]
    required_changes: list[str]
    revised_recommendations: list[str]
    round_number: int
    challenged_by: list[str]

    board_decision: dict[str, Any]  # CEO only — set in round 5
```

### Phase 3 — Deliberation (5 Rounds)

Managed by `DeliberationOrchestrator`. Each round invokes the relevant agents with a context-rich prompt compiled from all prior outputs. Challenges are consolidated: CEO round-1 challenges flow to CFO/CTO/CMO for round 2 responses; CMO round-3 challenges flow to round 4 revisions.

The system prompt for deliberation includes a modifier to put agents in "board meeting mode":

```python
DELIBERATION_MODIFIERS = {
    "ceo": "You are in an active board deliberation... "
           "Direct your questions at named roles.",
    "cfo": "Respond to challenges directly. Cite a number. "
           "State explicitly when you change your recommendation.",
    "cto": "State feasibility color: Green/Yellow/Red. "
           "Do not use 'complexity' as a shield — quantify it.",
    "cmo": "Name the customer segment. Be specific about pricing impact.",
}
```

### Phase 4 — Synthesis

Combines Phase 2 outputs, deliberation rounds 1-5, and the CEO's board decision into `board_report.md`. Injects the board decision near the top (before individual reports), followed by the full deliberation transcript, then individual reports.

---

## 📄 Output Structure

A `board_report.md` looks like this:

```markdown
# Executive Board Simulation Report

## Executive Summary
[One-line overview]

## Board Decision                          ← from CEO Round 5
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

## Deliberation Transcript                ← all 5 rounds visible
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
**CEO**: [synthesizes — the board_decision JSON was produced here]

## Individual Agent Reports               ← Phase 2 blind analysis
[CEO/CFO/CTO/CMO: title, summary, key findings, recommendations, risks]

## Action Items
- [HIGH/MEDIUM/LOW] [Task] | Owner: CFO | Due: TBD

## Overall Risk Assessment
- [CEO] [risk description]

## Risk Quantification
[Probability × Impact matrix + scored risks]
```

---

## 🔐 Security: Input Sanitization

All user prompts are sanitized before processing to mitigate prompt injection attacks:

```python
# src/utils.py - sanitize_prompt()
- Removes null bytes and control characters
- Filters common injection patterns (ignore instructions, new instructions:, etc.)
- Strips markdown image links that could inject context
- Normalizes whitespace
```

The sanitization runs automatically in the CLI pipeline before any prompt reaches the LLM.

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Runtime** | Python 3.10+ | Core language |
| **CLI Framework** | [Typer](https://typer.tiangolo.com/) | Clean CLI with rich formatting |
| **LLM Backend** | [Ollama](https://ollama.ai/) | Local AI inference (OpenAI-compatible API) |
| **LLM Models** | `google/gemma-4-e2b`, `llama3` (any OpenAI-compatible) | Language model |
| **Parsers** | `json5` | Relaxed JSON parsing (handles LLM sloppiness) |
| **Config** | `python-dotenv`, `pyyaml` | Settings and env management |
| **Output** | `markdown`, `requests` | Report generation, API calls |
| **Dev** | `pytest`, `black`, `ruff` | Testing and linting |

### LLM Client Design

The `AIClient` in `src/ai/client.py` uses a provider abstraction pattern:

1. **BaseProvider Interface** (`src/ai/abstract_provider.py`) — Abstract base class defining `complete()` and `complete_json()` methods
2. **OllamaProvider** (`src/ai/ollama_provider.py`) — Concrete implementation for local Ollama API
3. **4-layer JSON robustness pipeline** — Shared logic for handling malformed LLM output:
   - **Preprocess** — Strip markdown fences, bracket-matching to find JSON span, remove BOM/\x00
   - **Structural fixes** — Fix trailing commas, unescaped `\n`/`\r` inside strings, unquoted keys
   - **json5 fallback** — Try `json5.loads()` for relaxed JSON parsing
   - **Self-correction** — If all layers fail, re-call the LLM with a correction prompt (temp=0)

The provider pattern allows for future implementations (OpenAI, Anthropic, etc.) without changing the rest of the codebase.

---

## 📁 Project Structure

```
OpenExec/
├── src/
│   ├── __main__.py              # Module entry point
│   ├── cli.py                   # Typer CLI with all subcommands
│   │                           # Supports --assume, --weight, --no-memory
│   ├── main.py                  # write_report() — renders board_report.md
│   ├── orchestrator.py          # Orchestrator + SimulationState
│   │                           # Emits events to EventStore
│   ├── orchestrator_deliberation.py  # 5-round DeliberationOrchestrator
│   ├── events.py                # Event type definitions (event sourcing)
│   ├── event_store.py           # Append-only event persistence + replay
│   ├── agents/
│   │   ├── __init__.py          # AgentRegistry + register_default_agents()
│   │   ├── interface.py         # AgentReport dataclass
│   │   ├── templates_ceo.py      # CEO persona + analysis
│   │   ├── templates_cfo.py      # CFO persona + analysis
│   │   ├── templates_cto.py     # CTO persona + analysis
│   │   └── templates_cmo.py      # CMO persona + analysis
│   ├── ai/
│   │   ├── __init__.py          # Exports AIClient, prompt builders
│   │   ├── abstract_provider.py # BaseProvider abstract class
│   │   ├── ollama_provider.py   # OllamaProvider implementation
│   │   ├── client.py            # 4-layer JSON LLM client (delegates to provider)
│   │   └── prompts.py           # System prompts, routing, deliberation prompts
│   │                           # build_analysis_prompt() supports assumptions
│   ├── decision_tracker.py      # Logs to decisions/decision_*.json
│   ├── memory.py                 # Multi-session persistent memory
│   ├── feedback.py              # Agent rating + learning loop
│   ├── knowledge_base.py        # RAG document ingestion
│   ├── risk_analyzer.py          # Risk scoring + visual matrix
│   ├── export.py                # JSON/CSV/markdown action item export
│   ├── summary.py               # Executive summary generator
│   └── utils.py                 # Action item extraction + sanitize_prompt()
├── data/                        # Company data files
├── decisions/                   # Decision logs (auto-generated)
├── memory/                      # Memory index + conversation history
├── knowledge_base/              # Ingested KB documents + chunks
├── feedback/                    # Agent performance scores
├── graphify-out/               # Code knowledge graph (AST-only)
├── settings.json                # AI provider configuration
└── requirements.txt             # Python dependencies
```

---

## 🔮 Future Work

### Priority 4 — Automation
- **Scheduled analysis**: Run simulations on a cron schedule against tracked metrics
- **Trigger-based analysis**: Re-run deliberation when key metrics change (e.g., runway crosses a threshold)
- **Continuous monitoring dashboard**: Real-time view of open decisions and pending action items

### Priority 5 — Deeper Analysis
- **Real-time market data**: Full web fetching in the deliberation loop (currently disabled)
- **Financial modeling engine**: CFO gets a spreadsheet-grade model, not just narrative estimates
- **Market sizing & TAM analysis**: Automated total addressable market from initial inputs
- **Technical architecture diagrams**: CTO output includes generated system diagrams
- **Voting mechanism**: Weighted voting among agents with abstention tracking
- **Additional providers**: OpenAI, Anthropic provider implementations

### Contributing

Open to:
- **New agent personas**: COO (operations), CHRO (people), CLO (legal risk)
- **Real-time data source integrations**: FRED API for macro data, company financial APIs, news feeds
- **Improved deliberation prompts**: Prompt engineering to get more specific disagreements surfaced
- **Better risk modeling**: Monte Carlo simulation over the quantified risks
- **Export integrations**: Notion, Linear, Jira, Slack output formats

If you want to contribute:
1. Fork the repo
2. `black` format before committing
3. `ruff check .` passes clean
4. Run `openexec run "Your test scenario?"` and verify the board_report.md looks right