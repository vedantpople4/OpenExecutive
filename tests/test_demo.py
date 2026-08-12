"""Tests for openexec demo: canned run renders without an LLM."""

from openexec.demo_fixture import demo_results
from openexec.main import write_report
from openexec.report_html import render_html_report
from openexec.risk_analyzer import quantify_risks


def _rendered(tmp_path):
    results = quantify_risks(demo_results())
    out = tmp_path / "demo.md"
    write_report(results, str(out))
    html = render_html_report(results)
    return out.read_text(), html


class TestDemoFixture:
    def test_fixture_has_required_report_keys(self):
        results = demo_results()
        for key in ("executive_summary", "decision_point", "board_decision",
                    "agent_reports", "synthesized_recommendations",
                    "overall_risk_assessment"):
            assert key in results, f"demo fixture missing '{key}'"

    def test_fixture_has_all_four_cxos(self):
        agents = demo_results()["agent_reports"]
        assert {"ceo", "cfo", "cto", "cmo"} <= set(agents)

    def test_fixture_scores_are_realistic(self):
        for report in demo_results()["agent_reports"].values():
            assert 0 <= report["alignment_score"] <= 1
            assert report["is_fallback"] is False

    def test_demo_renders_markdown_and_html(self, tmp_path):
        text, html = _rendered(tmp_path)
        assert "Executive Board Simulation Report" in text
        assert "integration path" in text
        assert "<h1>Executive Board Simulation Report</h1>" in html

    def test_demo_risk_quantification_runs(self):
        results = quantify_risks(demo_results())
        assert len(results["quantified_risks"]) == 4
        assert results["risk_matrix"].startswith("Risk Matrix:")

    def test_no_fallback_badges_in_demo(self, tmp_path):
        text, html = _rendered(tmp_path)
        assert "FALLBACK STUB" not in text
        assert "FALLBACK STUB" not in html