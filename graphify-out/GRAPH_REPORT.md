# OpenExec Knowledge Graph Report

## Scan Date: 2026-06-13

## Architecture Overview

```
openexec/
├── orchestrator.py          # Core simulation workflow (Event Sourcing)
├── orchestrator_deliberation.py  # 5-round board meeting loop
├── agents/
│   ├── interface.py         # AgentReport dataclass (role-specific fields)
│   ├── register.py          # Agent registry (CEO, CFO, CTO, CMO)
├── knowledge_base.py        # RAG over company docs (JSON chunking)
├── memory.py               # Conversation memory (multi-session learning)
├── events.py               # Event types (EventType enum)
├── event_store.py         # Event storage (append-only, replayable)
├── summary.py              # Executive summary generation
├── risk_analyzer.py        # Risk quantification (probability/impact matrix)
├── feedback.py             # Feedback system (agent performance tracking)
├── export.py               # Action item export (JSON/CSV/markdown)
├── utils.py                # Sanitization, action item extraction
├── interactive.py          # Q&A mode for post-simulation discussion
└── cli.py                  # Typer CLI (setup, history, search, performance)
```

## Core Components

### 1. Orchestrator (orchestrator.py)
- Pattern: Event Sourcing
- Phases: Inception → Analysis → Deliberation → Synthesis
- State: SimulationState (UUID-based, event-driven)

### 2. Deliberation Loop (orchestrator_deliberation.py)
- Rounds: 5 total
- Round 1: CEO frames challenges
- Round 2: CFO, CTO respond
- Round 3: CMO raises market challenges
- Round 4: All agents revise positions
- Round 5: CEO synthesizes board_decision

### 3. Agent Registry (agents/register.py)
- Agents: CEO, CFO, CTO, CMO
- Role-specific fields in AgentReport
- Alignment scoring (0.0-1.0)

### 4. Knowledge Base (knowledge_base.py)
- RAG over company docs
- Categories: financials, pitch_deck, technical, etc.
- Chunking: sentence-based, 500 chars

### 5. Memory System (memory.py)
- Multi-session conversation storage
- Keyword-based search (future: embeddings)
- Decision history tracking

### 6. Event Store (event_store.py)
- Append-only event log
- Replayable state reconstruction
- Aggregate ID linking

## Agent Roles

| Agent | Responsibility | Key Fields |
|-------|---------------|------------|
| CEO | Strategic framing, synthesis | board_decision, challenges_for_* |
| CFO | Financials, capex/opex | capex_vs_opex, runway_impact_6mo |
| CTO | Technical stack, build cost | technical_verdict, vendor_lockin_risk |
| CMO | Market positioning, GTM | market_verdict, go_to_market_implication |

## Knowledge Graph Nodes

### Community 1: Core Simulation
- **orchestrator.py** - simulation workflow
- **event_store.py** - event logging
- **orchestrator_deliberation.py** - 5-round loop

### Community 2: Data & Memory
- **knowledge_base.py** - RAG
- **memory.py** - conversation storage
- **feedback.py** - agent performance tracking
- **export.py** - action item export

### Community 3: Agents & Data
- **agents/** - agent definitions
- **data/** - company docs (team_structure.md, industry_context.md)
- **decisions/** - decision logs

## Recent Decisions (Last 5)

1. 2026-06-13: AI infrastructure investment
2. 2026-06-08: Series A funding strategy
3. 2026-06-07: GPU capacity expansion
4. 2026-05-31: Product roadmap prioritization
5. 2026-05-30: Hiring plan adjustments

## Graph Status

- Nodes: ~150+
- Edges: ~300+
- Communities: 3 major clusters
- Last updated: 2026-06-02

## Next Steps

- Run `graphify update .` after code changes
- Add more company data to data/ directory
- Expand knowledge base with technical docs
