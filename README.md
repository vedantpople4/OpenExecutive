# OpenExec - Executive Board Simulation

> Run a strategic meeting in your head, but with real arguments.

**OpenExec** is a CLI tool that simulates a multi-round executive board deliberation on any business decision. It models four executives (CEO, CFO, CTO, CMO) — each optionally backed by their own team of specialist sub-agents — who debate, challenge, and revise their positions over five rounds, producing a synthesized board decision with explicit consensus, dissent, and action items.

**In short:** It replaces 3 hours of stakeholder meetings with a 60-second command - and gives you a report you can act on.

## Demo

https://github.com/user-attachments/assets/1e0799bc-539b-4e32-95a9-33257cdf833b

A literal, unstyled walkthrough of the real CLI — config, the `openexec run --teams
--research` command, the actual streamed hierarchical team deliberation, and the
generated `board_report.md` — captured live from an actual run of this tool, no
invented content. If the player above doesn't render for you, watch/download it
directly: [`videos/openexec-demo/renders/video.mp4`](videos/openexec-demo/renders/video.mp4)

**What do you get?**
A single, structured markdown file that includes:
*   **The Verdict:** The board's final decision and strategy.
*   **The Debate:** A full transcript of the five-round deliberation - where the agents agree, where they disagree, and why.
*   **The Report:** Independent analyses from each executive with key findings, risks, and how well each claim is grounded in real data.
*   **The Plan:** A list of prioritized, concrete action items with owners and deadlines.
*   **The Heatmap:** Quantified risks to help you focus on what matters.

## Quick Start

You need Python 3.10+ and a running local LLM (e.g., Ollama or LM Studio).

```bash
git clone https://github.com/vedantpople4/OpenExecutive.git
cd OpenExec
pip install -e .

# Set up your AI provider (Ollama, LM Studio, etc.)
openexec setup

# Run your first simulation
openexec run "Should we hire more Software Engineers or build AI agents to work?"
```

This will produce a `board_report.md` with the full board report.

## Core Features

- **Multi-Perspective LLM Debate:** CEO, CFO, CTO, and CMO argue from defined lenses (growth, numbers, feasibility, market). You get real disagreement, not a single opinion dressed four ways.
- **Hierarchical Teams (`--teams`):** Each executive can lead a real sub-team instead of speaking alone — CFO with a financial analyst, budget planner, and risk analyst; CTO with an engineering lead, solutions architect, and SRE; CMO with a growth marketer, content strategist, and SEO specialist; CEO with a chief of staff and strategy associate. Specialists analyze first, then their CXO synthesizes a team position before the board debate begins.
- **Live Research Grounding (`--research`):** Every agent's analysis can be checked against live web search plus your own knowledge base, weighted however you want. The report then tells you exactly how many of its numeric claims it could actually verify — not just how confident it sounds.
- **Honest Scoring:** Each agent report carries an `alignment_score` (renamed from `confidence_score`) measuring how well its position ties back to real data, not how sure the model sounds. If a model call fails to produce a valid response, the report says so explicitly instead of quietly faking a result.
- **Evolution of Arguments:** Agents revise their positions based on challenges from others. The CFO might revise their cost model after the CTO points out a hidden scaling bottleneck.
- **Deliberate Conflict, Not Consensus:** The system is designed to surface disagreements. The final report highlights not just what to do, but what open questions remain.
- **Context Preservation:** A Scribe agent maintains a running summary of the board's state, feeding it back into the LLM prompt so agents keep track of the argument across all five rounds.
- **Actionable Output:** Every recommendation leads to a trackable task with a clear owner and deadline.
- **Repeatable & Reproducible:** Run the same prompt twice and compare how the board's position changes based on new data or assumptions.

## Under the Hood (For Developers)

The engine is a state machine that manages a multi-round LLM conversation.

**Phase 1: Inception & Analysis**
The user prompt is classified into a category (infrastructure, pricing, market, etc.). Each agent receives a system prompt tailored to its role, along with the user's question, any data corpus, and (with `--research`) live web + knowledge-base grounding.

**Phase 2: Team Deliberation (`--teams` only)**
Each CXO's specialist sub-agents analyze independently, then the CXO synthesizes their team's position — before the board debate starts.

**Phase 3: Deliberation (5 Rounds)**
- **Round 1:** The CEO reads the independent reports and frames the debate, naming the core conflicts and directing specific questions to the other executives.
- **Round 2-4:** The CFO, CTO, and CMO respond to challenges, cross-reference each other's data, and revise their positions.
- **A Scribe agent synthesizes the board's state (consensus, conflicts, trajectory) after each round**, keeping context manageable across long deliberations.
- **Round 5:** The CEO synthesizes all inputs - consensus, dissent, and revised recommendations - into the final board decision.

**Phase 4: Synthesis**
The orchestrator assembles the final `board_report.md`, including the board decision, transcript, individual reports (each with a grounding/alignment score), and a quantified risk matrix.

**Key design decisions:**
- **Pure JSON:** All agent communication is structured JSON to ensure reliable parsing and downstream processing.
- **Context Engineering:** The Scribe's running summary lets the system handle long deliberations without hitting LLM token limits.
- **Honesty over polish:** A failed model call is disclosed in the report, never silently papered over.
- **Extensible:** New agents, new decision types, and new export formats can be added by extending the prompt templates and the orchestrator.

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Runtime** | Python 3.10+ | Core language |
| **CLI** | Typer (`typer`) | CLI with rich formatting |
| **LLM Backend** | Ollama / LM Studio | Local AI inference |
| **Research** | `ddgs` | Free live web search, no API key required |

## Usage

```bash
# Run a simulation
openexec run "Should we buy or lease new equipment?"

# Run with hierarchical sub-teams
openexec run "Should we launch a free tier?" --teams

# Ground every agent's claims in live web search + your knowledge base
openexec run "Should we expand to Europe?" --research --research-mix web=0.7,kb=0.3

# Run with assumptions
openexec run "Should we expand to Europe?" --assume market_growth=2%

# Run with weighted priorities
openexec run "Build vs buy?" --weight cfo=0.5 --weight cto=0.3

# Show help
openexec --help
```

See `openexec --help` for the full command reference, including counterfactual analysis, seeding, and batch runs.

## The Report

The output of a simulation is a `board_report.md`, structured as follows:

1.  **Executive Summary:** One-sentence overview of the board's position.
2.  **Decision:** Full board position with consensus, dissent, and action items.
3.  **Deliberation Transcript:** A markdown-formatted log of all five rounds, showing how the agents argued and revised their positions.
4.  **Individual Agent Reports:** Each executive's (and, with `--teams`, each specialist's) independent analysis, with a grounding count and alignment score.
5.  **Risk Quantification:** A scored risk matrix with specific probabilities and impact scores.
6.  **Data Sources:** A list of the data corpus used in the analysis.

This is the document you take to your board, your investors, or your team.
