"""Tests for openexec/summary.py — executive summary generation."""

import pytest
from openexec.summary import generate_executive_summary, write_executive_summary


@pytest.fixture
def sample_results():
    """Sample simulation results for testing."""
    return {
        "executive_summary": "Executive Board Analysis for: Buy vs lease equipment",
        "decision_point": "Decision required for: Buy vs lease equipment",
        "synthesized_recommendations": [
            "[CEO] Implement the strategy",
            "[CFO] Allocate budget for Q2",
            "[CTO] Build the infrastructure",
            "[CMO] Launch marketing campaign",
            "[CEO] Establish timeline",
            "[CFO] Monitor expenses"
        ],
        "overall_risk_assessment": [
            "Risk 1: Budget overrun",
            "Risk 2: Timeline delay",
            "Risk 3: Technical challenges",
            "Risk 4: Market conditions"
        ],
        "agent_reports": {
            "ceo": {
                "title": "CEO Report",
                "alignment_score": 0.8,
                "key_findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Rec 1", "Rec 2"]
            },
            "cfo": {
                "title": "CFO Report",
                "alignment_score": 0.7,
                "key_findings": ["Finding A", "Finding B"],
                "recommendations": ["Rec A"]
            },
            "cto": {
                "title": "CTO Report",
                "alignment_score": 0.9,
                "key_findings": ["Finding X"],
                "recommendations": ["Rec X"]
            },
            "cmo": {
                "title": "CMO Report",
                "alignment_score": 0.6,
                "key_findings": ["Finding Y"],
                "recommendations": ["Rec Y"]
            }
        },
        "data_sources": {
            "access_success_rate": 0.85,
            "timestamp": "2024-01-01T00:00:00"
        }
    }


class TestGenerateExecutiveSummary:
    """generate_executive_summary() — generating executive summary from results."""

    def test_generates_summary(self, sample_results):
        """Should generate executive summary."""
        summary = generate_executive_summary(sample_results)
        assert summary is not None
        assert len(summary) > 0

    def test_includes_title(self, sample_results):
        """Should include title."""
        summary = generate_executive_summary(sample_results)
        assert "# Executive Summary" in summary

    def test_includes_decision(self, sample_results):
        """Should include decision."""
        summary = generate_executive_summary(sample_results)
        assert "Buy vs lease equipment" in summary
        assert "**Decision:**" in summary

    def test_strips_executive_board_prefix(self, sample_results):
        """Should strip 'Executive Board Analysis for:' prefix."""
        summary = generate_executive_summary(sample_results)
        assert "Executive Board Analysis for:" not in summary

    def test_includes_decision_point_section(self, sample_results):
        """Should include decision point section."""
        summary = generate_executive_summary(sample_results)
        assert "## Decision Point" in summary
        assert "Buy vs lease equipment" in summary

    def test_strips_decision_required_prefix(self, sample_results):
        """Should strip 'Decision required for:' prefix."""
        summary = generate_executive_summary(sample_results)
        assert "Decision required for:" not in summary

    def test_includes_top_recommendations(self, sample_results):
        """Should include top 5 recommendations."""
        summary = generate_executive_summary(sample_results)
        assert "## Top Recommendations" in summary
        assert "1. [CEO] Implement the strategy" in summary
        assert "5. [CEO] Establish timeline" in summary

    def test_limits_recommendations_to_5(self, sample_results):
        """Should limit recommendations to top 5."""
        summary = generate_executive_summary(sample_results)
        # Should have exactly 5 recommendations numbered 1-5
        lines = summary.split("\n")
        # Find the Top Recommendations section and count items there
        in_rec_section = False
        rec_count = 0
        for line in lines:
            if "## Top Recommendations" in line:
                in_rec_section = True
            elif in_rec_section and line.startswith("##"):
                break
            elif in_rec_section and line.strip() and not line.startswith("-"):
                # Count recommendation lines (non-empty, non-list, non-header)
                if any(line.strip().startswith(f"{i}. ") for i in range(1, 6)):
                    rec_count += 1
        assert rec_count == 5, f"Expected 5 recommendations, found {rec_count}: {lines[30:40]}"

    def test_includes_critical_risks(self, sample_results):
        """Should include critical risks section."""
        summary = generate_executive_summary(sample_results)
        assert "## Critical Risks" in summary
        assert "1. Risk 1: Budget overrun" in summary
        assert "3. Risk 3: Technical challenges" in summary

    def test_limits_risks_to_3(self, sample_results):
        """Should limit risks to top 3."""
        summary = generate_executive_summary(sample_results)
        # Should have 3 numbered risks
        lines = summary.split("\n")
        risk_lines = [l for l in lines if l.strip().startswith(("1.", "2.", "3.")) and "Risk" in l]
        assert len(risk_lines) == 3

    def test_includes_agent_confidence(self, sample_results):
        """Should include agent confidence scores."""
        summary = generate_executive_summary(sample_results)
        assert "## Agent Confidence" in summary
        assert "**CEO:**" in summary
        assert "**CFO:**" in summary
        assert "**CTO:**" in summary
        assert "**CMO:**" in summary

    def test_formats_confidence_as_percentage(self, sample_results):
        """Should format confidence scores as percentages."""
        summary = generate_executive_summary(sample_results)
        assert "80%" in summary  # CEO's 0.8
        assert "70%" in summary  # CFO's 0.7
        assert "90%" in summary  # CTO's 0.9
        assert "60%" in summary  # CMO's 0.6

    def test_includes_data_sources_when_present(self, sample_results):
        """Should include data sources when present."""
        summary = generate_executive_summary(sample_results)
        assert "## Data Sources" in summary
        assert "85%" in summary  # access_success_rate
        assert "2024-01-01T00:00:00" in summary

    def test_omits_data_sources_when_missing(self):
        """Should omit data sources section when missing."""
        results = {
            "executive_summary": "Test",
            "decision_point": "Test",
            "synthesized_recommendations": ["Rec 1"],
            "overall_risk_assessment": ["Risk 1"],
            "agent_reports": {}
        }
        summary = generate_executive_summary(results)
        assert "## Data Sources" not in summary

    def test_includes_next_steps(self, sample_results):
        """Should include next steps section."""
        summary = generate_executive_summary(sample_results)
        assert "## Next Steps" in summary
        assert "action items identified" in summary

    def test_counts_action_items(self, sample_results):
        """Should count action items correctly."""
        summary = generate_executive_summary(sample_results)
        assert "6 action items identified" in summary

    def test_handles_empty_recommendations(self):
        """Should handle empty recommendations list."""
        results = {
            "executive_summary": "Test",
            "decision_point": "Test",
            "synthesized_recommendations": [],
            "overall_risk_assessment": ["Risk 1"],
            "agent_reports": {}
        }
        summary = generate_executive_summary(results)
        assert "0 action items identified" in summary

    def test_handles_empty_risks(self):
        """Should handle empty risks list."""
        results = {
            "executive_summary": "Test",
            "decision_point": "Test",
            "synthesized_recommendations": ["Rec 1"],
            "overall_risk_assessment": [],
            "agent_reports": {}
        }
        summary = generate_executive_summary(results)
        assert "## Critical Risks" in summary
        # Should not have numbered risks
        lines = summary.split("\n")
        risk_lines = [l for l in lines if l.strip().startswith(("1.", "2.", "3.")) and "Risk" in l]
        assert len(risk_lines) == 0

    def test_handles_missing_agent_reports(self):
        """Should handle missing agent reports."""
        results = {
            "executive_summary": "Test",
            "decision_point": "Test",
            "synthesized_recommendations": ["Rec 1"],
            "overall_risk_assessment": ["Risk 1"],
            "agent_reports": {}
        }
        summary = generate_executive_summary(results)
        assert "## Agent Confidence" in summary
        # Should not have any agent listed
        assert "**CEO:**" not in summary

    def test_handles_missing_fields(self):
        """Should handle missing fields gracefully."""
        results = {}
        summary = generate_executive_summary(results)

        # Should not crash
        assert "# Executive Summary" in summary
        assert "## Decision Point" in summary
        assert "## Top Recommendations" in summary
        assert "## Critical Risks" in summary
        assert "## Agent Confidence" in summary
        assert "## Next Steps" in summary


class TestWriteExecutiveSummary:
    """write_executive_summary() — writing executive summary to file."""

    def test_writes_summary_to_file(self, sample_results, tmp_path):
        """Should write summary to file."""
        output_path = tmp_path / "summary.md"
        write_executive_summary(sample_results, str(output_path))

        assert output_path.exists()

    def test_file_contains_summary(self, sample_results, tmp_path):
        """File should contain the generated summary."""
        output_path = tmp_path / "summary.md"
        write_executive_summary(sample_results, str(output_path))

        with open(output_path, 'r') as f:
            content = f.read()

        assert "# Executive Summary" in content
        assert "Buy vs lease equipment" in content

    def test_overwrites_existing_file(self, sample_results, tmp_path):
        """Should overwrite existing file."""
        output_path = tmp_path / "summary.md"

        # Write initial content
        with open(output_path, 'w') as f:
            f.write("Old content")

        # Write summary
        write_executive_summary(sample_results, str(output_path))

        with open(output_path, 'r') as f:
            content = f.read()

        assert "Old content" not in content
        assert "# Executive Summary" in content
