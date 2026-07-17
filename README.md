# OpenExec - Executive Board Simulation

> Run a strategic meeting in your head, but with real arguments.

**OpenExec** is a CLI tool that simulates a multi-round executive board deliberation on any business decision. It models four distinct AI agents (CEO, CFO, CTO, CMO) who debate, challenge, and revise their positions over five rounds, producing a synthesized board decision with explicit consensus, dissent, and action items. 

**In short:** It replaces 3 hours of stakeholder meetings with a 60-second command - and gives you a report you can act on.

## Demo

<!--
  GitHub renders an inline <video> player when the src is a raw.githubusercontent.com
  URL to a file committed in this repo — no manual upload step needed, unlike a plain
  relative path (which only renders as a download link). This points at the
  `adding-teams` branch; once merged, update the branch segment to `main`.
-->
<video src="https://raw.githubusercontent.com/vedantpople4/OpenExecutive/adding-teams/videos/openexec-promo/renders/video.mp4" controls muted width="720"></video>

70s overview: the board's hierarchical teams, live research grounding, and a real
decision (with dissent) from this project's own `board_report.md`. If the player
above doesn't render for you, watch/download it directly:
[`videos/openexec-promo/renders/video.mp4`](videos/openexec-promo/renders/video.mp4)

**What do you get?**
A single, structured markdown file that includes:
*   **The Verdict:** The board's final decision and strategy.
*   **The Debate:** A full transcript of the five-round deliberation - where the agents agree, where they disagree, and why.
*   **The Report:** Independent analyses from each executive with key findings and risks.
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

## See It in Action

Imagine you're considering international expansion. Instead of scheduling a meeting to get everyone aligned, you just run a command:

```bash
openexec run "Should we expand to Europe?"
```

A few seconds later, OpenExec delivers a complete strategic report, including:

*   **Board Decision:** A clear statement like "The board agrees that immediate survival depends on locking down the MVP scope to target one high - value segment."
*   **The Debate: A Round-by-Round Transcript:**
    *   **Round 1 (CEO):** Frames the strategic conflicts. *"The immediate decision hinges on whether we prioritize rapid market capture or foundational stability."*
    *   **Round 2 (CFO &amp; CTO):** Respond with data-driven positions. *"We cannot treat systemic scaling issues as abstract liabilities; they must be quantified as fixed CapEx costs."*
    *   **Round 3 (CMO):** Raises market challenges. *"This is your turn to respond - and to raise challenges of your own."*
    *   **Round 4 (All):** Revise recommendations based on the debate. *"I require a detailed, line-item breakdown from the CTO outlining exactly which features are absolutely required to achieve the minimum viable PoC."*
    *   **Round 5 (CEO):** Synthesizes the final verdict. *"The board is committed to moving forward with an AI Proof-of-Concept."*

*   **Consensus:** What everyone agrees on.
*   **Dissent:** What they can't agree on, and why.
*   **Risk:** A scored risk matrix with specific probabilities and impacts.
*   **Action Items:** What to do, who owns it, and when it's due.

## Core Features

- **Multi-Perspective LLM Debate:** CEO, CFO, CTO, and CMO argue from defined lenses (growth, numbers, feasibility, market). You get real disagreement, not a single opinion dressed four ways.
- **Evolution of Arguments:** Agents revise their positions based on challenges from others. The CFO might revise their cost model after the CTO points out a hidden scaling bottleneck.
- **Deliberate Conflict, Not Consensus:** The system is designed to surface disagreements. The final report highlights not just what to do, but what the open questions remain.
- **Context Preservation:** A Scribe agent maintains a running summary of the board's state, feeding it back into the LLM prompt to ensure the agents keep track of the thread of the argument across all five rounds.
- **Actionable Output:** Every recommendation leads to a trackable task with a clear owner and deadline.
- **Repeatable &amp; Reproducible:** You can run the same prompt twice and compare how the board's position changes based on new data or assumptions.

## Under the Hood (For Developers)

The engine is a state machine that manages a multi-round LLM conversation.

**Phase 1: Inception &amp; Analysis**  
The user prompt is classified into a category (infrastructure, pricing, market, etc.). Each agent receives a system prompt tailored to its role, along with the user's question and any uploaded data corpus.

**Phase 2: Deliberation (5 Rounds)**  
- **Round 1:** The CEO reads the independent reports and frames the debate, naming the core conflicts and directing specific questions to the other executives.
- **Round 2-4:** The CFO, CTO, and CMO respond to challenges, cross-reference each other's data, and revise their positions. 
- **A Scribe agent synthesizes the board's state (consensus, conflicts, trajectory) after each round.** This lean summary is injected into subsequent prompts to keep context manageable and prevent LLM overflow.
- **Round 5:** The CEO synthesizes all inputs - consensus, dissent, and revised recommendations - into the final board decision.

**Phase 3: Synthesis**  
The orchestrator assembles the final `board_report.md`, including the board decision, transcript, individual reports, and a quantified risk matrix.

**Key design decisions:**
- **Pure JSON:** All agent communication is structured JSON to ensure reliable parsing and downstream processing.
- **Context Engineering:** By using the Scribe to keep a running summary, the system can handle long deliberations without hitting LLM token limits, ensuring the agents always have the full thread of the argument.
- **Extensible:** New agents, new decision types, and new export formats can be added by extending the prompt templates and the orchestrator.

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Runtime** | Python 3.10+ | Core language |
| **CLI** | Typer (`typer`) | CLI with rich formatting |
| **LLM Backend** | Ollama / LM Studio | Local AI inference |
## Usage

See the full command reference in the CLI for advanced options like counterfactual analysis ("What if our budget was 10x larger?") and weighted agent priorities.

```bash
# Run a simulation
openexec run "Should we buy or lease new equipment?"

# Run with assumptions
openexec run "Should we expand to Europe?" --assume market_growth=2%

# Run with weighted priorities
openexec run "Build vs buy?" --weight cfo=0.5 --weight cto=0.3

# Show help
openexec --help
```

## The Report

The output of a simulation is a `board_report.md`, structured as follows:

1.  **Executive Summary:** One-sentence overview of the board's position.
2.  **Decision:** Full board position with consensus, dissent, and action items.
3.  **Deliberation Transcript:** A markdown-formatted log of all five rounds, showing how the agents argued and revised their positions.
4.  **Individual Agent Reports:** The original independent analyses from each executive.
5.  **Risk Quantification:** A scored risk matrix with specific probabilities and impact scores.
6.  **Data Sources:** A list of the data corpus used in the analysis.

This is the document you take to your board, your investors, or your team.
