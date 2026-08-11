"""Tests for openexec.compare: decision loading and diffing."""

import json

import pytest

from openexec.compare import describe_decision, diff_decisions, list_decisions, load_decision


@pytest.fixture
def decision_dir(tmp_path):
    """Create a decision_log.json plus two decision files."""
    old = {
        "timestamp": "20260701_100000",
        "prompt": "Should we hire more engineers?",
        "results": {
            "executive_summary": "Hire a lean team now.",
            "board_decision": {
                "consensus_points": ["Growth first", "Manage burn"],
                "dissent_points": ["Hire senior only"],
            },
            "overall_risk_assessment": ["[CFO] Burn risk high"],
            "agent_reports": {
                "ceo": {"alignment_score": 0.8},
                "cfo": {"alignment_score": 0.6},
            },
        },
        "action_items": [
            {"priority": "HIGH", "task": "Post two job reqs"},
            {"priority": "MEDIUM", "task": "Cut one vendor"},
        ],
    }
    new = {
        "timestamp": "20260731_100000",
        "prompt": "Should we hire more engineers?",
        "results": {
            "executive_summary": "Hire a lean team now, but cap at three.",
            "board_decision": {
                "consensus_points": ["Growth first"],
                "dissent_points": ["Hire senior only", "Outsource QA"],
            },
            "overall_risk_assessment": ["[CTO] Scaling risk late"],
            "agent_reports": {
                "ceo": {"alignment_score": 0.9},
                "cfo": {"alignment_score": 0.5},
                "cmo": {"alignment_score": 0.7},
            },
        },
        "action_items": [
            {"priority": "HIGH", "task": "Post two job reqs"},
            {"priority": "HIGH", "task": "Post three job reqs"},
        ],
    }
    records = {
        "old": (old, f"decision_{old['timestamp']}.json"),
        "new": (new, f"decision_{new['timestamp']}.json"),
    }
    for rec, name in records.values():
        (tmp_path / name).write_text(json.dumps(rec))
    log = [
        {"timestamp": rec["timestamp"], "prompt": rec["prompt"], "file_path": name}
        for rec, name in records.values()
    ]
    (tmp_path / "decision_log.json").write_text(json.dumps(log))
    return tmp_path


class TestLoadDecision:
    def test_load_by_path(self, decision_dir):
        rec = load_decision(str(decision_dir / "decision_20260731_100000.json"))
        assert rec["prompt"] == "Should we hire more engineers?"
        assert "results" in rec and "action_items" in rec

    def test_load_by_timestamp(self, decision_dir):
        rec = load_decision("20260701_100000", log_dir=str(decision_dir))
        assert rec["timestamp"] == "20260701_100000"

    def test_load_by_index_1_is_most_recent(self, decision_dir):
        rec = load_decision(1, log_dir=str(decision_dir))
        assert rec["timestamp"] == "20260731_100000"

    def test_load_by_index_2(self, decision_dir):
        rec = load_decision(2, log_dir=str(decision_dir))
        assert rec["timestamp"] == "20260701_100000"

    def test_missing_reference_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_decision("does-not-exist", log_dir=str(tmp_path))

    def test_unknown_index_raises(self, decision_dir):
        with pytest.raises(FileNotFoundError):
            load_decision(99, log_dir=str(decision_dir))


class TestDiffDecisions:
    def test_prompt_matching(self, decision_dir):
        old = load_decision(2, log_dir=str(decision_dir))
        new = load_decision(1, log_dir=str(decision_dir))
        diff = diff_decisions(old, new)
        assert diff["same_prompt"] is True

    def test_consensus_removed_and_kept(self, decision_dir):
        diff = diff_decisions(
            load_decision(2, log_dir=str(decision_dir)),
            load_decision(1, log_dir=str(decision_dir)),
        )
        # "Manage burn" dropped from consensus
        assert "Manage burn" in diff["consensus_removed"]
        # nothing added to consensus
        assert diff["consensus_added"] == []

    def test_dissent_added(self, decision_dir):
        diff = diff_decisions(
            load_decision(2, log_dir=str(decision_dir)),
            load_decision(1, log_dir=str(decision_dir)),
        )
        assert "Outsource QA" in diff["dissent_added"]

    def test_action_items(self, decision_dir):
        diff = diff_decisions(
            load_decision(2, log_dir=str(decision_dir)),
            load_decision(1, log_dir=str(decision_dir)),
        )
        assert "Cut one vendor" in diff["actions_removed"]
        assert "Post three job reqs" in diff["actions_added"]
        # shared item not reported either way
        assert all("Post two job reqs" not in x for x in (diff["actions_added"], diff["actions_removed"]))

    def test_risk_delta(self, decision_dir):
        diff = diff_decisions(
            load_decision(2, log_dir=str(decision_dir)),
            load_decision(1, log_dir=str(decision_dir)),
        )
        assert "[CFO] Burn risk high" in diff["risks_removed"]
        assert "[CTO] Scaling risk late" in diff["risks_added"]

    def test_agent_score_deltas(self, decision_dir):
        diff = diff_decisions(
            load_decision(2, log_dir=str(decision_dir)),
            load_decision(1, log_dir=str(decision_dir)),
        )
        scores = {s["agent"]: s for s in diff["agent_scores"]}
        assert scores["ceo"]["delta"] == 0.1
        assert scores["cfo"]["delta"] == -0.1
        # new agent appears with old=None
        assert scores["cmo"]["old"] is None
        assert scores["cmo"]["new"] == 0.7

    def test_prompt_difference_detected(self, decision_dir):
        old = load_decision(2, log_dir=str(decision_dir))
        new = load_decision(1, log_dir=str(decision_dir))
        new["prompt"] = "Should we buy or lease?"
        assert diff_decisions(old, new)["same_prompt"] is False


class TestListDecisions:
    def test_most_recent_first(self, decision_dir):
        decisions = list_decisions(limit=10, log_dir=str(decision_dir))
        assert len(decisions) == 2
        assert decisions[0]["timestamp"] == "20260731_100000"
        assert decisions[1]["timestamp"] == "20260701_100000"

    def test_respects_limit(self, decision_dir):
        decisions = list_decisions(limit=1, log_dir=str(decision_dir))
        assert len(decisions) == 1
        assert decisions[0]["timestamp"] == "20260731_100000"

    def test_empty_log(self, tmp_path):
        assert list_decisions(log_dir=str(tmp_path)) == []


class TestDescribeDecision:
    def test_renders_verdict_actions_risks(self, decision_dir):
        rec = load_decision(1, log_dir=str(decision_dir))
        text = describe_decision(rec)
        assert "Should we hire more engineers?" in text
        assert "Hire a lean team now, but cap at three." in text
        assert "Post three job reqs" in text
        assert "[CTO] Scaling risk late" in text
        assert "CEO:0.90" in text and "CFO:0.50" in text

    def test_index_header(self, decision_dir):
        rec = load_decision(1, log_dir=str(decision_dir))
        text = describe_decision(rec, index=1, total=2)
        assert "[1/2] 2026-07-31" in text