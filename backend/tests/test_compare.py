from decimal import Decimal

from app.config import get_settings
from app.db import get_dynamodb_resource


def _put_decision(run_id, prompt, board_decision, action_items, risks, agent_reports):
    table = get_dynamodb_resource().Table(get_settings().decisions_table)
    table.put_item(
        Item={
            "id": run_id,
            "entity_type": "DECISION",
            "status": "completed",
            "created_at": "2026-01-01T00:00:00.000Z",
            "prompt": prompt,
            "executive_summary": f"Summary for {run_id}",
            "board_decision": board_decision,
            "action_items": action_items,
            "overall_risk_assessment": risks,
            "agent_reports": agent_reports,
        }
    )


def test_compare_two_decisions(client):
    _put_decision(
        "run-old",
        "Expand into APAC",
        board_decision={"consensus_points": ["Ship MVP first"], "dissent_points": ["Budget too tight"]},
        action_items=[{"priority": "HIGH", "task": "Hire regional lead", "owner": "CEO", "due_date": "2026-02-01"}],
        risks=["Currency exposure"],
        agent_reports={
            "ceo": {"alignment_score": Decimal("0.6")},
            "cfo": {"alignment_score": Decimal("0.4")},
        },
    )
    _put_decision(
        "run-new",
        "Expand into APAC",
        board_decision={"consensus_points": ["Ship MVP first", "Partner locally"], "dissent_points": []},
        action_items=[
            {"priority": "HIGH", "task": "Hire regional lead", "owner": "CEO", "due_date": "2026-02-01"},
            {"priority": "MEDIUM", "task": "Sign local partner", "owner": "CMO", "due_date": "2026-03-01"},
        ],
        risks=["Currency exposure", "Regulatory delay"],
        agent_reports={
            "ceo": {"alignment_score": Decimal("0.8")},
            "cfo": {"alignment_score": Decimal("0.4")},
        },
    )

    response = client.get("/compare", params={"old": "run-old", "new": "run-new"})
    assert response.status_code == 200
    body = response.json()

    assert body["same_prompt"] is True
    assert body["consensus_added"] == ["Partner locally"]
    assert body["consensus_removed"] == []
    assert body["dissent_removed"] == ["Budget too tight"]
    assert body["actions_added"] == ["Sign local partner"]
    assert body["risks_added"] == ["Regulatory delay"]

    scores = {d["agent"]: d for d in body["agent_scores"]}
    assert scores["ceo"]["delta"] == 0.2
    assert scores["cfo"]["delta"] == 0.0


def test_compare_missing_decision_returns_404(client):
    response = client.get("/compare", params={"old": "does-not-exist", "new": "also-missing"})
    assert response.status_code == 404
