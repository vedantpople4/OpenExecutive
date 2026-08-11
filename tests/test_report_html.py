"""Tests for openexec.report_html: standalone HTML report rendering."""

from openexec.report_html import render_html_report


def _results():
    return {
        "executive_summary": "Hire a lean team now.",
        "board_decision": {
            "summary": "Commit to the integration path.",
            "consensus_points": ["Growth first"],
            "dissent_points": ["Hire senior only"],
        },
        "synthesized_recommendations": ["[CEO] Post two job reqs"],
        "overall_risk_assessment": ["[CFO] Burn risk high"],
        "risk_matrix": "Risk Matrix:\n  HIGH  P70",
        "agent_reports": {
            "ceo": {
                "title": "Growth analysis",
                "summary": "We must grow.",
                "key_findings": ["Team is thin"],
                "recommendations": ["Hire two"],
                "risks": ["Burn"],
                "alignment_score": 0.8,
            },
            "cto": {
                "title": "Failed analysis",
                "is_fallback": True,
                "summary": "stub",
                "alignment_score": 0.0,
            },
        },
    }


class TestRenderHtmlReport:
    def test_contains_top_level_sections(self):
        html_out = render_html_report(_results())
        assert "<h1>Executive Board Simulation Report</h1>" in html_out
        assert "<h2>Executive Summary</h2>" in html_out
        assert "<h2>Board Decision</h2>" in html_out
        assert "<h2>Action Items</h2>" in html_out
        assert "<h2>Risk Quantification</h2>" in html_out
        assert "<h2>Agent Reports</h2>" in html_out

    def test_renders_board_decision_content(self):
        html_out = render_html_report(_results())
        assert "Commit to the integration path." in html_out
        assert "Growth first" in html_out
        assert "Hire senior only" in html_out

    def test_renders_agent_reports_and_scores(self):
        html_out = render_html_report(_results())
        assert "CEO Report" in html_out
        assert "Alignment Score: 0.80" in html_out
        assert "Growth analysis" in html_out

    def test_fallback_badge(self):
        html_out = render_html_report(_results())
        assert "FALLBACK STUB" in html_out

    def test_action_items_rendered(self):
        html_out = render_html_report(_results())
        assert "Post two job reqs" in html_out

    def test_risk_matrix_preserved(self):
        html_out = render_html_report(_results())
        assert "Risk Matrix:" in html_out

    def test_escapes_model_text(self):
        results = _results()
        results["executive_summary"] = "<script>alert('xss')</script>"
        html_out = render_html_report(results)
        assert "<script>alert('xss')</script>" not in html_out
        assert "&lt;script&gt;" in html_out

    def test_self_contained_no_external_assets(self):
        html_out = render_html_report(_results())
        assert "http://" not in html_out and "https://" not in html_out
        assert "src=" not in html_out
        assert "<style>" in html_out and "</style>" in html_out

    def test_empty_results_render(self):
        html_out = render_html_report({})
        assert "<h1>Executive Board Simulation Report</h1>" in html_out
        assert "No action items identified." in html_out