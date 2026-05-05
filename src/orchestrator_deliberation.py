"""Deliberation orchestration — multi-round board meeting workflow."""

from typing import Any, Dict

from src.agents.interface import AgentReport


# ------------------------------------------------------------------
# Phase layout: which agents speak in each round
# ------------------------------------------------------------------
PHASE_ROUNDS: Dict[int, tuple[str, ...]] = {
    1: ("ceo",),
    2: ("cfo", "cto"),
    3: ("cmo",),
    4: ("cfo", "cto", "cmo"),
    5: ("ceo",),  # synthesis only
}


class DeliberationOrchestrator:
    """Runs the multi-round deliberation loop.

    Each round compiles the prior outputs, builds an appropriate prompt
    for the participating agents, and stores their AgentReport results
    keyed by round number in ``state.deliberation_outputs``.

    The final board decision is produced by the CEO in round 5 and
    written back into state so run_synthesis() can surface it.
    """

    def __init__(self, state: "SimulationState", registry) -> None:
        self.state = state
        self.registry = registry
        self._ai_client = None
        self._ai_clients: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run_deliberation(self) -> None:
        """Run all 5 deliberation rounds and store results in state."""
        from src.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS

        self._init_ai_clients()

        # The Phase-2 blind reports are the basis for round-1 framing.
        # Store them under round-key 0 so all round builders can access them.
        self.state.deliberation_outputs[0] = {
            name: self._report_to_dict(report)
            for name, report in self.state.agent_outputs.items()
            if isinstance(report, AgentReport)
        }

        for round_num in range(1, 6):
            print(f"\n{'='*50}")
            print(f"DELIBERATION ROUND {round_num}")
            print(f"{'='*50}")

            if round_num == 5:
                self._run_ceo_synthesis()
            else:
                self._run_delegation_round(round_num)

            self.state.deliberation_round = round_num

        print("\n--- All deliberation rounds complete ---")

    # ------------------------------------------------------------------
    # Round delegation
    # ------------------------------------------------------------------

    def _run_delegation_round(self, round_num: int) -> None:
        """Call each agent listed in PHASE_ROUNDS[round_num] for this round."""
        from src.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS

        agents = PHASE_ROUNDS.get(round_num, ())
        round_outputs: Dict[str, AgentReport] = {}

        for agent_name in agents:
            print(f"  -> {agent_name.upper()} speaking...")
            try:
                report = self._call_agent(agent_name, round_num)
                round_outputs[agent_name] = report
                # Track challenges directed at this agent
                if round_num == 1 and agent_name == "ceo":
                    self._consolidate_challenges(1, round_outputs)
            except Exception as e:
                print(f"  [WARN] {agent_name.upper()} deliberation failed: {e}")

        self.state.deliberation_outputs[round_num] = round_outputs

    # ------------------------------------------------------------------
    # CEO synthesis
    # ------------------------------------------------------------------

    def _run_ceo_synthesis(self) -> None:
        """Run CEO's round-5 synthesis to produce board_decision."""
        from src.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS
        from src.ai.prompts import get_agent_system_prompt

        print("  -> CEO synthesising board decision...")
        try:
            report = self._call_agent("ceo", 5)
            r5_dict = self._report_to_dict(report)
            # Persist the board_decision to state so run_synthesis can find it
            self.state.deliberation_outputs[5] = {"ceo": report}
            print("  [OK] Board decision produced — writing to state.")
        except Exception as e:
            print(f"  [WARN] CEO synthesis failed: {e}")

    # ------------------------------------------------------------------
    # Agent invocation
    # ------------------------------------------------------------------

    def _call_agent(self, agent_name: str, round_num: int) -> AgentReport:
        """Build prompt, call LLM, return AgentReport.

        Falls back to a hardcoded stub if the AI call fails so the loop
        never crashes a running simulation on a single bad round.
        """
        from src.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS
        from src.ai.client import AIClient

        client = self._get_ai_client(agent_name)
        deliberation_prompt = build_deliberation_prompt(
            agent_name=agent_name,
            round_num=round_num,
            core_prompt=self.state.core_prompt,
            prior_outputs=self._reports_to_dicts(self.state.deliberation_outputs),
            challenges=self.state.challenges,
        )
        system_prompt = self._get_system_prompt(agent_name)

        try:
            ai_response = client.complete_json_with_retry(
                prompt=deliberation_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
            )
            agent_report = AgentReport.from_llm_response(agent_name, ai_response)
            agent_report.round_number = round_num
            return agent_report
        except Exception as e:
            print(f"  [FALLBACK] LLM failed for {agent_name} round {round_num}: {e}")
            return self._hardcoded_deliberation_report(agent_name, round_num)

    def _build_base_prompt(self, agent_name: str, round_num: int) -> str:
        """Returns a short contextual prefix (not used directly in prompts; retained for extension)."""
        return f"[{agent_name.upper()} deliberation round {round_num}]"

    # ------------------------------------------------------------------
    # System prompt composition
    # ------------------------------------------------------------------

    def _get_system_prompt(self, agent_name: str) -> str:
        from src.ai.prompts import get_agent_system_prompt
        from src.ai import DELIBERATION_MODIFIERS
        base = get_agent_system_prompt(agent_name)
        modifier = DELIBERATION_MODIFIERS.get(agent_name, "")
        return base + modifier

    # ------------------------------------------------------------------
    # Challenges consolidation (CEO round 1 → other agents)
    # ------------------------------------------------------------------

    def _consolidate_challenges(self, round_num: int, outputs: Dict[str, AgentReport]) -> None:
        """Pull challenges_for_cfo/cto/cmo from CEO's round-1 output into state.challenges."""
        ceo_report = outputs.get("ceo")
        if not ceo_report:
            return

        self.state.challenges["cfo"] = list(ceo_report.challenges_for_cfo)
        self.state.challenges["cto"] = list(ceo_report.challenges_for_cto)
        self.state.challenges["cmo"] = list(ceo_report.challenges_for_cmo)
        print(f"  CEO framed challenges: CFO={len(ceo_report.challenges_for_cfo)} "
              f"CTO={len(ceo_report.challenges_for_cto)} "
              f"CMO={len(ceo_report.challenges_for_cmo)}")

    # ------------------------------------------------------------------
    # AI client management (lazy, one per agent)
    # ------------------------------------------------------------------

    def _get_ai_client(self, agent_name: str) -> "AIClient":
        if agent_name not in self._ai_clients:
            from src.ai.client import AIClient
            self._ai_clients[agent_name] = AIClient()
        return self._ai_clients[agent_name]

    def _init_ai_clients(self) -> None:
        """Pre-warm AI clients so failures surface before the loop runs."""
        for agent_name in ("ceo", "cfo", "cto", "cmo"):
            try:
                self._get_ai_client(agent_name)
            except Exception as e:
                print(f"[WARN] AI client unavailable for {agent_name}: {e}")

    # ------------------------------------------------------------------
    # Report conversion
    # ------------------------------------------------------------------

    def _report_to_dict(self, report: AgentReport) -> Dict[str, Any]:
        return {
            ** {
                "title": report.title,
                "summary": report.summary,
                "key_findings": report.key_findings,
                "recommendations": report.recommendations,
                "risks": report.risks,
                "alignment_score": report.alignment_score,
                "round_number": report.round_number,
            },
            ** report.get_role_specific_fields(),
        }

    # ------------------------------------------------------------------
    # Hardcoded fallback report
    # ------------------------------------------------------------------

    def _hardcoded_deliberation_report(self, agent_name: str, round_num: int) -> AgentReport:
        """Return a minimal AgentReport when the LLM is unavailable."""
        summaries = {
            1: f"{agent_name.upper()} frames board; challenges directed at peers.",
            2: f"{agent_name.upper()} responds to CEO's questions and cross-references peer.",
            3: "CMO raises market challenges to CFO and CTO.",
            4: f"{agent_name.upper()} revises position per challenges received.",
            5: "CEO synthesizes board decision from all rounds.",
        }
        return AgentReport(
            title=f"{agent_name.upper()} Deliberation — Round {round_num}",
            summary=summaries.get(round_num, ""),
            round_number=round_num,
            alignment_score=0.5,
        )

    # ------------------------------------------------------------------
    # Report conversion helpers
    # ------------------------------------------------------------------

    def _reports_to_dicts(
        self,
        outputs: Dict[int, Dict[str, Any]],
    ) -> Dict[int, Dict[str, Any]]:
        """Convert AgentReport objects to dicts so build_deliberation_prompt can use .get()."""
        result: Dict[int, Dict[str, Any]] = {}
        for rnd, agents in outputs.items():
            result[rnd] = {}
            for name, val in agents.items():
                if isinstance(val, AgentReport):
                    result[rnd][name] = self._report_to_dict(val)
                else:
                    result[rnd][name] = val
        return result
        """Return a minimal AgentReport when the LLM is unavailable."""
        summaries = {
            1: f"{agent_name.upper()} frames board; challenges directed at peers.",
            2: f"{agent_name.upper()} responds to CEO's questions and cross-references peer.",
            3: "CMO raises market challenges to CFO and CTO.",
            4: f"{agent_name.upper()} revises position per challenges received.",
            5: "CEO synthesizes board decision from all rounds.",
        }
        return AgentReport(
            title=f"{agent_name.upper()} Deliberation — Round {round_num}",
            summary=summaries.get(round_num, ""),
            round_number=round_num,
            alignment_score=0.5,
        )