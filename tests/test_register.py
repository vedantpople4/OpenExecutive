"""Tests for openexec.register: decision register aggregation."""

import json

import pytest

from openexec.register import build_register


@pytest.fixture
def register_dir(tmp_path):
    """Three decision records with a shared recurring risk and varied dates."""
    records = [
        {
            "timestamp": "20260701_100000",
            "prompt": "Should we hire?",
            "results": {
                "overall_risk_assessment": ["[CFO] Burn risk high", "[CTO] Scaling risk late"],
                "agent_reports": {"ceo": {"alignment_score": 0.8}, "cfo": {"alignment_score": 0.6}},
            },
            "action_items": [
                {"priority": "HIGH", "task": "Post reqs"},
                {"priority": "MEDIUM", "task": "Cut vendor"},
            ],
        },
        {
            "timestamp": "20260715_100000",
            "prompt": "Should we hire?",
            "results": {
                "overall_risk_assessment": ["[CFO] Burn risk high"],
                "agent_reports": {"ceo": {"alignment_score": 0.9}, "cmo": {"alignment_score": 0.7}},
            },
            "action_items": [{"priority": "HIGH", "task": "Post reqs"}],
        },
        {
            "timestamp": "20260801_100000",
            "prompt": "Should we expand?",
            "results": {
                "overall_risk_assessment": ["[CFO] Cash flow tight"],
                "agent_reports": {"ceo": {"alignment_score": 0.7}},
            },
            "action_items": [],
        },
    ]
    log = []
    for rec in records:
        name = f"decision_{rec['timestamp']}.json"
        (tmp_path / name).write_text(json.dumps(rec))
        log.append({"timestamp": rec["timestamp"], "prompt": rec["prompt"], "file_path": name})
    (tmp_path / "decision_log.json").write_text(json.dumps(log))
    return tmp_path


class TestBuildRegister:
    def test_counts(self, register_dir):
        reg = build_register(log_dir=str(register_dir))
        assert reg["total_decisions"] == 3
        assert reg["distinct_prompts"] == 2
        assert reg["total_action_items"] == 3
        assert reg["high_priority_actions"] == 2

    def test_top_risks_recurrence(self, register_dir):
        reg = build_register(log_dir=str(register_dir))
        top = reg["top_risks"]
        assert top[0]["text"] == "[cfo] burn risk high"
        assert top[0]["count"] == 2

    def test_agent_alignment_mean(self, register_dir):
        reg = build_register(log_dir=str(register_dir))
        assert reg["agent_alignment"]["ceo"]["mean"] == 0.8  # (0.8+0.9+0.7)/3
        assert reg["agent_alignment"]["ceo"]["samples"] == 3
        assert reg["agent_alignment"]["cfo"]["mean"] == 0.6

    def test_per_month(self, register_dir):
        reg = build_register(log_dir=str(register_dir))
        months = {m["month"]: m["count"] for m in reg["per_month"]}
        assert months["202608"] == 1
        assert months["202607"] == 2

    def test_most_recent(self, register_dir):
        reg = build_register(log_dir=str(register_dir))
        assert reg["most_recent"] == "20260801_100000"

    def test_empty_dir(self, tmp_path):
        reg = build_register(log_dir=str(tmp_path))
        assert reg["total_decisions"] == 0
        assert reg["total_action_items"] == 0
        assert reg["agent_alignment"] == {}

    def test_empty_log_file(self, tmp_path):
        (tmp_path / "decision_log.json").write_text(json.dumps([]))
        reg = build_register(log_dir=str(tmp_path))
        assert reg["total_decisions"] == 0