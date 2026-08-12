"""Tests for openexec.main.write_report — the markdown report renderer.

This is the primary user-facing deliverable and was the least-covered module
(1%). Every report section must render without crashing and include its content.
"""

from openexec.main import write_report
from openexec.utils import extract_action_items
from tests.fixtures import sample_results


def _render(results, tmp_path):
    out = tmp_path / "report.md"
    write_report(results, str(out))
    return out.read_text()


class TestWriteReportSections:
    def test_title_and_executive_summary(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "# Executive Board Simulation Report" in text
        assert "Commit to the integration path for Q2 revenue." in text

    def test_fallback_warnings(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "Data Integrity Warning" in text
        assert "cfo (round 2)" in text
        assert "hardcoded placeholder stub" in text

    def test_board_decision_sections(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "We commit to the integration path." in text
        assert "Growth first" in text
        assert "Hire senior only" in text
        assert "Post reqs now" in text
        assert "If burn exceeds 20%, freeze hiring" in text
        assert "CTO wants depth first" in text

    def test_deliberation_rounds(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "Round 1" in text
        assert "Frame the debate" in text
        assert "Speed vs depth" in text

    def test_agent_reports(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "CEO Report" in text
        assert "Growth analysis" in text
        assert "Hire two engineers" in text
        assert "Burn rate rising 20%" in text

    def test_fallback_badge_in_agent_report(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "FALLBACK STUB" in text
        assert "cto" in text.lower()

    def test_grounding_line(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "2/3 numeric claims found in source data" in text
        assert "$2m" in text

    def test_alignment_score_interpretations(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "0.80" in text and "High confidence" in text
        assert "0.00" in text and "Low confidence" in text

    def test_action_items_section(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "Action Items" in text
        assert "Post two job reqs" in text

    def test_risk_sections(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "Overall Risk Assessment" in text
        assert "Burn risk high" in text

    def test_data_sources(self, tmp_path):
        text = _render(sample_results(), tmp_path)
        assert "Data Sources" in text
        assert "90.0%" in text
        assert "data/company_background.md" in text
        assert "example.com" in text

    def test_empty_results_does_not_crash(self, tmp_path):
        text = _render({}, tmp_path)
        assert "No action items identified." in text


class TestNoFallbackRendering:
    def test_without_fallbacks(self, tmp_path):
        results = sample_results()
        results.pop("fallback_warnings")
        text = _render(results, tmp_path)
        assert "Data Integrity Warning" not in text

    def test_without_deliberation(self, tmp_path):
        results = sample_results()
        results.pop("deliberation_rounds")
        text = _render(results, tmp_path)
        assert "Deliberation Transcript" not in text

    def test_without_risk_matrix(self, tmp_path):
        results = sample_results()
        results.pop("risk_matrix", None)
        results["overall_risk_assessment"] = []
        text = _render(results, tmp_path)
        assert "Risk Quantification" not in text


class TestExtractActionItemsIntegration:
    def test_actions_from_synthesized_recs(self):
        items = extract_action_items(sample_results())
        tasks = [i["task"] for i in items]
        assert any("Post two job reqs" in t for t in tasks)
        assert any("Cut one vendor" in t for t in tasks)

    def test_fallback_agent_recommendations_skipped(self):
        results = sample_results()
        results["agent_reports"]["cto"]["recommendations"] = ["Build 50 servers"]
        items = extract_action_items(results)
        tasks = [i["task"] for i in items]
        assert all("50 servers" not in t for t in tasks)
