"""Tests for openexec.risk_analyzer — probability/impact scoring and matrix."""

from openexec.risk_analyzer import RiskQuantifier, quantify_risks


class TestQuantifyRisk:
    def test_keyword_risk(self):
        q = RiskQuantifier()
        result = q.quantify_risk("[CFO] Burn risk high")
        assert result["probability"] == 0.7
        assert result["impact"] == 9  # burn(8) + 1 for [CFO]
        assert result["risk_score"] == 0.7 * 9
        assert result["priority"] == "MEDIUM"  # 6.3 < 7

    def test_explicit_probability_tag_overrides(self):
        q = RiskQuantifier()
        result = q.quantify_risk("Market risk with probability: Low")
        assert result["probability"] == 0.2

    def test_unknown_risk_defaults(self):
        q = RiskQuantifier()
        result = q.quantify_risk("Something unusual happened")
        assert result["probability"] == 0.5
        assert result["impact"] == 5
        assert result["priority"] == "LOW"  # 0.5*5=2.5 < 4

    def test_priority_bands(self):
        q = RiskQuantifier()
        assert q._get_priority(8) == "HIGH"
        assert q._get_priority(5) == "MEDIUM"
        assert q._get_priority(2) == "LOW"


class TestRiskMatrix:
    def test_matrix_contains_risk_and_legend(self):
        q = RiskQuantifier()
        matrix = q.generate_risk_matrix(["[CFO] Burn risk high", "[CEO] Runway at risk"])
        assert "Risk Matrix:" in matrix
        assert "Legend:" in matrix
        assert "IMPACT ->" in matrix
        assert "## Quantified Risks" in matrix

    def test_empty_risks(self):
        q = RiskQuantifier()
        matrix = q.generate_risk_matrix([])
        assert "Risk Matrix:" in matrix
        assert "Quantified Risks" in matrix


class TestQuantifyRisks:
    def test_attaches_quantified_risks_and_matrix(self):
        results = {
            "overall_risk_assessment": [
                "[CFO] Burn risk high",
                "[CTO] Scaling risk late",
            ]
        }
        out = quantify_risks(results)
        assert len(out["quantified_risks"]) == 2
        assert out["risk_matrix"].startswith("Risk Matrix:")
        # sorted by risk_score descending
        scores = [r["risk_score"] for r in out["quantified_risks"]]
        assert scores == sorted(scores, reverse=True)

    def test_missing_risks(self):
        out = quantify_risks({})
        assert out["quantified_risks"] == []
        assert "Risk Matrix:" in out["risk_matrix"]
