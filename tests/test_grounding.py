"""Tests for openexec.grounding — numeric-claim extraction and corpus checking."""

from openexec.grounding import check_report_grounding, extract_numeric_claims


class TestExtractNumericClaims:
    def test_currency_claims(self):
        assert "$2m" in extract_numeric_claims("Revenue of $2m")
        assert "$1,200" in extract_numeric_claims("Cost of $1,200")

    def test_percent_claims(self):
        assert "20%" in extract_numeric_claims("Burn rising 20%")

    def test_time_span_claims(self):
        claims = extract_numeric_claims("Ship in 3 months, 2 weeks to review")
        assert "3 months" in claims
        assert "2 weeks" in claims

    def test_bare_numbers_skipped(self):
        assert extract_numeric_claims("round 2 of 5, 3 conflicts") == []

    def test_unit_claims(self):
        assert "40ms" in extract_numeric_claims("latency 40ms")

    def test_duplicates_in_text(self):
        # raw extraction returns both; dedup happens at the report level
        assert extract_numeric_claims("$2m now and $2m later") == ["$2m", "$2m"]

    def test_dedup_at_report_level(self):
        report = {"summary": "$2m now and $2m later"}
        corpus = {"doc": "needs $2m"}
        result = check_report_grounding(report, corpus)
        assert result["claims_checked"] == 1
        assert result["claims_grounded"] == 1


class TestCheckReportGrounding:
    def test_grounded_and_ungrounded(self):
        report = {
            "summary": "We need $2m by Q2.",
            "key_findings": ["Costs are 20% higher"],
            "risks": ["Growth is $1m"],
        }
        corpus = {"doc": "The company needs $2m and costs rose 20%."}
        result = check_report_grounding(report, corpus)
        assert result["claims_checked"] == 3
        assert result["claims_grounded"] == 2
        assert "$1m" in result["ungrounded"]

    def test_empty_corpus_returns_empty(self):
        report = {"summary": "We need $2m."}
        assert check_report_grounding(report, {}) == {}

    def test_no_claims_returns_empty(self):
        report = {"summary": "We should grow."}
        corpus = {"doc": "anything"}
        assert check_report_grounding(report, corpus) == {}

    def test_normalization_ignores_format(self):
        report = {"summary": "Revenue hits $2 m."}
        corpus = {"doc": "Revenue hits $2m."}
        result = check_report_grounding(report, corpus)
        assert result["claims_grounded"] == 1
        assert result["ungrounded"] == []
