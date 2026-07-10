"""Deliberation orchestration — multi-round board meeting workflow."""

from typing import Any, Dict

from openexec.agents.interface import AgentReport


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

    def __init__(self, state: "SimulationState", registry, verbose: bool = False) -> None:
        self.state = state
        self.registry = registry
        self._ai_client = None
        self._ai_clients: Dict[str, Any] = {}
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run_deliberation(self) -> None:
        """Run dynamic deliberation rounds and store results in state."""
        from openexec.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS
        from openexec.ai.prompts import SCRIBE_SYSTEM_PROMPT

        self._init_ai_clients()

        # The Phase-2 blind reports are the basis for round-1 framing.
        self.state.deliberation_outputs[0] = {
            name: self._report_to_dict(report)
            for name, report in self.state.agent_outputs.items()
            if isinstance(report, AgentReport)
        }

        round_num = 1
        max_rounds = 10
        converged = False

        # Minimum round before convergence check: 2 when only 2 agents active, else 3
        active = getattr(self.state, 'active_agents', None) or []
        min_convergence_round = 2 if len([a for a in active if a != "ceo"]) <= 1 else 3

        while round_num <= max_rounds and not converged:
            print(f"\n[bold]Progress: Round {round_num}/{max_rounds}[/bold]")

            if round_num == 1:
                self._run_delegation_round(round_num)
            elif round_num >= min_convergence_round and self._check_convergence(round_num - 1):
                # Converged early — run CEO synthesis before exiting
                print("  [Converged after round {}]".format(round_num - 1))
                self._run_ceo_synthesis()
                converged = True
                break
            elif round_num >= 5:
                # Always attempt CEO synthesis by round 5
                self._run_ceo_synthesis()
                converged = True
                break
            else:
                had_participants = self._run_delegation_round(round_num)
                if had_participants:
                    self._update_board_summary(round_num)

            self.state.deliberation_round = round_num
            round_num += 1

        if round_num > max_rounds:
            print("\n[yellow]Max rounds reached without explicit convergence. Forcing synthesis.[/yellow]")
            self._run_ceo_synthesis()

        print("\n[green]✓ Deliberation rounds complete[/green]")

    # ------------------------------------------------------------------
    # Verbose dump helpers
    # ------------------------------------------------------------------

    def _dump_agent_report(self, agent_name: str, round_num: int, report) -> None:
        from openexec.ai.prompts import get_agent_system_prompt

        header_color = "green" if agent_name == "ceo" else "cyan"
        print(f"     [bold {header_color}]── {agent_name.upper()} Round {round_num} ──[/bold {header_color}]")
        if getattr(report, "summary", None):
            print(f"     summary : {report.summary}")
        if getattr(report, "position", None):
            print(f"     position: {report.position}")
        rc = getattr(report, "required_changes", None) or []
        for c in rc:
            print(f"     req chg : {c}")
        rks = getattr(report, "risks", None) or []
        for r in rks:
            print(f"     risk    : {r}")
        kf = getattr(report, "key_findings", None) or []
        for k in kf:
            print(f"     finding : {k}")
        cf = getattr(report, "challenges_for", None) or {}
        for tgt, items in cf.items():
            for it in items:
                print(f"     →{tgt}: {it}")

        # Synthesized-board-decision fields (CEO round 5)
        for attr in ("decision", "consensus_statement", "consensus_points", "final_actions", "contingencies"):
            val = getattr(report, attr, None)
            if not val:
                continue
            if isinstance(val, str):
                print(f"     [green]{attr}[/green]: {val}")
            elif isinstance(val, list):
                for item in val:
                    print(f"     [green]{attr}[/green]: {item}")

    # ------------------------------------------------------------------
    # Round delegation
    # ------------------------------------------------------------------

    def _run_delegation_round(self, round_num: int) -> bool:
        """Call agents for this round, dynamically selected based on conflicts and active_agents.

        Returns True if at least one agent participated, False if the round was skipped entirely
        (e.g. when filtering reduces the participant list to zero for targeted simulations).
        """
        from openexec.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS

        # 1. Base agents for the round from fixed layout
        all_agents_this_round = PHASE_ROUNDS.get(round_num, ())

        # 2. Limit by active_agents (targeted simulation)
        agents_to_invite = list(all_agents_this_round)
        if hasattr(self.state, 'active_agents') and self.state.active_agents:
            agents_to_invite = [a for a in all_agents_this_round if a in self.state.active_agents]

        # 3. Early-exit when no active agents are scheduled for this round
        if not agents_to_invite:
            print(f"  [Skipping round {round_num} — no active agents scheduled]")
            return False

        # 4. Dynamic Pruning (Skip agents if no conflicts/required changes involve them in previous round)
        if round_num >= 2:
            prior_round = self.state.deliberation_outputs.get(round_num - 1, {})
            involved_agents = set()

            # Check conflicts/required_changes in all reports from last round
            for report in prior_round.values():
                if isinstance(report, AgentReport):
                    # Mentioned in conflicts?
                    for conflict in report.conflicts:
                        for agent in ["cfo", "cto", "cmo"]:
                            if agent.upper() in conflict.upper():
                                involved_agents.add(agent)
                    # Mentioned in required changes?
                    for change in report.required_changes:
                        for agent in ["cfo", "cto", "cmo"]:
                            if agent.upper() in change.upper():
                                involved_agents.add(agent)

            # If a round typically has agents but none are "involved", keep the default to avoid empty rounds
            if involved_agents:
                agents_to_invite = [a for a in agents_to_invite if a in involved_agents or a == "ceo"]
            else:
                # Fallback to requested active agents for this round if no specific conflicts found
                pass

        round_outputs: Dict[str, AgentReport] = {}

        for agent_name in agents_to_invite:
            print(f"  -> {agent_name.upper()} speaking...")
            try:
                report = self._call_agent(agent_name, round_num)
                round_outputs[agent_name] = report
                if self.verbose:
                    self._dump_agent_report(agent_name, round_num, report)
                # Track challenges directed at this agent
                if round_num == 1 and agent_name == "ceo":
                    self._consolidate_challenges(1, round_outputs)
            except Exception as e:
                print(f"  [WARN] {agent_name.upper()} deliberation failed: {e}")

        self.state.deliberation_outputs[round_num] = round_outputs
        return bool(round_outputs)

    # ------------------------------------------------------------------
    # CEO synthesis
    # ------------------------------------------------------------------

    def _run_ceo_synthesis(self) -> None:
        """Run CEO's round-5 synthesis to produce board_decision."""
        from openexec.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS
        from openexec.ai.prompts import get_agent_system_prompt

        print("  -> CEO synthesising board decision...")
        try:
            report = self._call_agent("ceo", 5)
            r5_dict = self._report_to_dict(report)
            # Persist the board_decision to state so run_synthesis can find it
            self.state.deliberation_outputs[5] = {"ceo": report}
            print("  [OK] Board decision produced — writing to state.")
            if self.verbose:
                self._dump_agent_report("ceo", 5, report)
        except Exception as e:
            print(f"  [WARN] CEO synthesis failed: {e}")

    # ------------------------------------------------------------------
    # Agent invocation
    # ------------------------------------------------------------------

    def _call_agent(self, agent_name: str, round_num: int) -> AgentReport:
        """Build prompt, call LLM, return AgentReport.

        Tries a lean context first, falls back to a simplified prompt if it fails,
        and only then uses the hardcoded stub.
        """
        from openexec.ai import build_deliberation_prompt, DELIBERATION_MODIFIERS
        from openexec.ai.client import AIClient

        client = self._get_ai_client(agent_name)

        active_agents = getattr(self.state, 'active_agents', None) or []

        # Attempt 1: Lean Context (Scribe Summary + R-1 + R0)
        try:
            deliberation_prompt = build_deliberation_prompt(
                agent_name=agent_name,
                round_num=round_num,
                core_prompt=self.state.core_prompt,
                prior_outputs=self._reports_to_dicts(self.state.deliberation_outputs),
                challenges=self.state.challenges,
                board_summary=self.state.board_summary,
                active_agents=active_agents,
            )
            system_prompt = self._get_system_prompt(agent_name)

            ai_response = client.complete_json_with_retry(
                prompt=deliberation_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
            )
            agent_report = AgentReport.from_llm_response(agent_name, ai_response)
            agent_report.round_number = round_num
            if self.verbose:
                print(f"     [dim]prompt sys {len(system_prompt)}t | usr {len(deliberation_prompt)}t | t=0.7[/dim]")
            return agent_report

        except Exception as e:
            print(f"  [RETRY] Lean context failed for {agent_name} round {round_num}: {e}. Trying simplified prompt...")

            # Attempt 2: Simplified Context (Round 3+ only)
            if round_num >= 3:
                try:
                    # Prune prior_outputs to only include the most recent round and blind reports
                    raw_outputs_0 = self.state.deliberation_outputs.get(0, {})
                    raw_outputs_r = self.state.deliberation_outputs.get(round_num - 1, {})
                    simplified_outputs = {
                        0: {k: self._report_to_dict(v) if isinstance(v, AgentReport) else v for k, v in raw_outputs_0.items()},
                        round_num - 1: {k: self._report_to_dict(v) if isinstance(v, AgentReport) else v for k, v in raw_outputs_r.items()},
                    }

                    simplified_prompt = build_deliberation_prompt(
                        agent_name=agent_name,
                        round_num=round_num,
                        core_prompt=self.state.core_prompt,
                        prior_outputs=simplified_outputs,
                        challenges=self.state.challenges,
                        board_summary=self.state.board_summary,
                        active_agents=active_agents,
                    )

                    ai_response = client.complete_json_with_retry(
                        prompt=simplified_prompt,
                        system_prompt=system_prompt,
                        temperature=0.3, # Lower temp for stability
                    )
                    agent_report = AgentReport.from_llm_response(agent_name, ai_response)
                    agent_report.round_number = round_num
                    return agent_report
                except Exception as e2:
                    print(f"  [FAIL] Simplified prompt also failed for {agent_name} round {round_num}: {e2}")

            print(f"  [FALLBACK] Final failure for {agent_name} round {round_num}. Using stub.")
            return self._hardcoded_deliberation_report(agent_name, round_num)

    def _update_board_summary(self, round_num: int) -> None:
        """Call Scribe agent to synthesize current round's outputs into state.board_summary."""
        from openexec.ai.prompts import SCRIBE_SYSTEM_PROMPT
        from openexec.ai.client import AIClient

        print(f"  -> Scribe synthesizing round {round_num} summary...")
        client = AIClient()

        # Gather raw materials for the scribe: current summary + new round reports
        current_summary = self.state.board_summary or "No prior summary exists. Start the record."
        round_reports = self.state.deliberation_outputs.get(round_num, {})

        # Convert reports to a readable format for the scribe
        reports_text = []
        for name, report in round_reports.items():
            if isinstance(report, AgentReport):
                reports_text.append(f"Agent {name.upper()} wrote: {report.summary}")
            else:
                reports_text.append(f"Agent {name.upper()} wrote: {report.get('summary', 'N/A')}")

        scribe_prompt = (
            f"Current Board Summary:\n{current_summary}\n\n"
            f"Reports from Round {round_num}:\n" + "\n".join(reports_text) +
            "\n\nUpdate the board summary based on these new inputs. Maintain the four required sections."
        )

        try:
            ai_response = client.complete_json_with_retry(
                prompt=scribe_prompt,
                system_prompt=SCRIBE_SYSTEM_PROMPT,
                temperature=0.3,
            )
            # complete_json_with_retry already returns a parsed dict
            if isinstance(ai_response, dict):
                data = ai_response
            elif isinstance(ai_response, str):
                import json
                data = json.loads(ai_response)
            else:
                data = ai_response

            self.state.board_summary = data.get("board_summary", self.state.board_summary)
            print("  [OK] Board summary updated.")
            if self.verbose:
                new_summary = self.state.board_summary or ""
                print(f"     [magenta]SCRIBE R{round_num}[/magenta]  {len(current_summary)}→{len(new_summary)} chars")
                print(f"     excerpt: {new_summary[:240]}…")
        except Exception as e:
            print(f"  [WARN] Scribe failed to update summary: {e}")

    # ------------------------------------------------------------------
    # System prompt composition
    # ------------------------------------------------------------------

    def _get_system_prompt(self, agent_name: str) -> str:
        from openexec.ai.prompts import get_agent_system_prompt
        from openexec.ai import DELIBERATION_MODIFIERS
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
            from openexec.ai.client import AIClient
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
        return report.to_dict()

    def _check_convergence(self, round_num: int) -> bool:
        """Check if the deliberation has converged.

        Convergence is reached if:
        1. Round is >= min_convergence_round (2 for two-agent sims, 3 otherwise).
        2. The CEO explicitly signals convergence in their latest report.
        3. Alignment scores are consistently high (> 0.8) and conflicts are empty.
        """
        active = getattr(self.state, 'active_agents', None) or []
        min_round = 2 if len([a for a in active if a != "ceo"]) <= 1 else 3
        if round_num < min_round:
            return False

        current_reports = self.state.deliberation_outputs.get(round_num, {})
        if not current_reports:
            return False

        # 1. CEO explicit signal
        ceo_report = current_reports.get("ceo")
        if ceo_report and hasattr(ceo_report, "board_decision") and ceo_report.board_decision:
            decision = ceo_report.board_decision
            if decision.get("status") == "converged" or decision.get("final_decision"):
                return True

        # 2. Stability / Alignment check
        reports = [r for r in current_reports.values() if isinstance(r, AgentReport)]
        if not reports:
            return False

        all_aligned = all(r.alignment_score >= 0.8 for r in reports)
        no_conflicts = all(not r.conflicts for r in reports)

        return all_aligned and no_conflicts

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
            is_fallback=True,
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