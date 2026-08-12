"""Full-pipeline integration test for `openexec run` with a mock LLM.

Runs the complete simulation end-to-end — inception, analysis, deliberation,
synthesis, report rendering, event emission, memory + decision logging —
against a canned JSON responder, so CI exercises the real orchestrator wiring
headlessly (the gap test_cli.py leaves by skipping the live-LLM path).
"""

import json

import pytest

from openexec.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def _canned_payload():
    """One JSON dict that satisfies every phase's response schema.

    AgentReport.from_llm_response uses .get() everywhere, so a rich superset
    works for inception, analysis, team synthesis, all deliberation rounds, and
    the scribe (which reads board_summary). CEO round 5 needs board_decision.
    """
    return {
        "title": "Mock Analysis",
        "summary": "The board should pursue the integration path for Q2 revenue.",
        "key_findings": ["Revenue first", "Runway protected"],
        "recommendations": ["Approve the 30-day pilot"],
        "risks": ["Partner lock-in", "Pilot underdelivers"],
        "alignment_score": 0.8,
        "strategic_verdict": "integration",
        "financial_verdict": "integration",
        "technical_verdict": "integration",
        "market_verdict": "integration",
        "agreements": ["Growth matters"],
        "conflicts": ["Speed vs depth"],
        "required_changes": ["Cap pilot spend"],
        "revised_recommendations": ["Pilot first"],
        "challenges_for_cfo": ["Justify runway math"],
        "challenges_for_cto": ["Prove scale"],
        "challenges_for_cmo": ["Show demand"],
        "board_decision": {
            "summary": "Commit to integration for Q2.",
            "consensus_points": ["Revenue first", "Runway protected"],
            "dissent_points": ["CTO wants depth first"],
            "final_priority_actions": ["Approve the 30-day pilot"],
            "dissenting_opinions": ["CTO argues depth"],
            "contingencies": ["If pilot < 40%, revisit the platform build"],
        },
        "board_summary": "The board is leaning integration.",
    }


class MockAIClient:
    """Drop-in for AIClient: every completion returns the canned payload."""

    runtime_overrides = {}

    def __init__(self, provider=None, settings_path=None):
        pass

    def complete_json_with_retry(self, prompt, system_prompt=None, max_tokens=None,
                                 temperature=None, max_attempts=2):
        return _canned_payload()

    def complete_json(self, prompt, system_prompt=None, max_tokens=None, temperature=None):
        return _canned_payload()

    def complete(self, prompt, system_prompt=None, max_tokens=None, temperature=None):
        return json.dumps(_canned_payload())


@pytest.fixture
def isolated_run(tmp_path, monkeypatch):
    """Run in a clean dir with a settings.json and AIClient fully mocked."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "settings.json").write_text(json.dumps({
        "ai": {"base_url": "http://localhost:11434/v1", "model": "mock"},
        "agents": {"enabled": ["ceo", "cfo", "cto", "cmo"]},
    }))
    monkeypatch.setattr("openexec.ai.client.AIClient", MockAIClient)
    monkeypatch.setattr("openexec.ai.AIClient", MockAIClient)

    # The module globals create their dirs at import time (repo cwd). Root
    # fresh instances in the isolated dir so nothing writes back to the repo.
    from openexec.memory import MemorySystem
    from openexec.decision_tracker import DecisionTracker
    from openexec.cli import memory_system as cli_memory, decision_tracker as cli_tracker
    fresh_memory = MemorySystem(memory_dir=str(tmp_path / "memory"))
    fresh_tracker = DecisionTracker(log_dir=str(tmp_path / "decisions"))
    monkeypatch.setattr(cli_memory, "memory_dir", fresh_memory.memory_dir)
    monkeypatch.setattr(cli_memory, "index_path", fresh_memory.index_path)
    monkeypatch.setattr(cli_memory, "index", fresh_memory.index)
    monkeypatch.setattr(cli_tracker, "log_dir", fresh_tracker.log_dir)
    monkeypatch.setattr(cli_tracker, "decision_log_file", fresh_tracker.decision_log_file)
    return tmp_path


class TestFullRunPipeline:
    def test_run_produces_report(self, isolated_run):
        result = runner.invoke(app, [
            "run", "Should we build or integrate?", "-o", "report.md",
        ])
        assert result.exit_code == 0, result.output
        assert (isolated_run / "report.md").exists()
        text = (isolated_run / "report.md").read_text()
        assert "# Executive Board Simulation Report" in text
        assert "integration path" in text

    def test_run_reports_no_fallback_stubs(self, isolated_run):
        result = runner.invoke(app, [
            "run", "Should we build or integrate?", "-o", "report.md",
        ])
        assert result.exit_code == 0, result.output
        assert "FALLBACK STUB" not in (isolated_run / "report.md").read_text()

    def test_run_emits_events(self, isolated_run):
        runner.invoke(app, ["run", "Should we build or integrate?", "-o", "report.md"])
        events_dir = isolated_run / "memory" / "events"
        assert events_dir.exists()
        assert len(list(events_dir.glob("*.json"))) > 0

    def test_run_logs_decision(self, isolated_run):
        runner.invoke(app, ["run", "Should we build or integrate?", "-o", "report.md"])
        assert (isolated_run / "decisions" / "decision_log.json").exists()

    def test_run_html_flag(self, isolated_run):
        result = runner.invoke(app, [
            "run", "Should we build or integrate?", "-o", "report.md", "--html",
        ])
        assert result.exit_code == 0, result.output
        html = (isolated_run / "report.html")
        assert html.exists()
        assert "<h1>Executive Board Simulation Report</h1>" in html.read_text()

    def test_run_research_flag_does_not_crash(self, isolated_run, monkeypatch):
        # --research adds web/KB context; stub it out to avoid network.
        monkeypatch.setattr(
            "openexec.research.build_research_context",
            lambda *a, **k: ("## Research context\nno live sources.", {"research_sources": []}),
        )
        result = runner.invoke(app, [
            "run", "Should we build or integrate?", "-o", "report.md", "--research",
        ])
        assert result.exit_code == 0, result.output

    def test_run_teams_flag_does_not_crash(self, isolated_run):
        result = runner.invoke(app, [
            "run", "Should we build or integrate?", "-o", "report.md", "--teams",
        ])
        assert result.exit_code == 0, result.output
        assert "FALLBACK STUB" not in (isolated_run / "report.md").read_text()

    def test_board_decision_in_report(self, isolated_run):
        runner.invoke(app, ["run", "Should we build or integrate?", "-o", "report.md"])
        text = (isolated_run / "report.md").read_text()
        assert "Commit to integration for Q2." in text
        assert "Consensus Points" in text

    def test_no_memory_flag_skips_storage(self, isolated_run):
        runner.invoke(app, [
            "run", "Should we build or integrate?", "-o", "report.md", "--no-memory",
        ])
        conv_dir = isolated_run / "memory" / "conversations"
        # The directory exists (MemorySystem creates it); no conversation is stored.
        assert not list(conv_dir.glob("*.json"))
