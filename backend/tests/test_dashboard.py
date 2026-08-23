from decimal import Decimal

from app.config import get_settings
from app.db import get_dynamodb_resource


def _put_decision(run_id, prompt, created_at, action_items, risks, agent_reports):
    table = get_dynamodb_resource().Table(get_settings().decisions_table)
    table.put_item(
        Item={
            "id": run_id,
            "entity_type": "DECISION",
            "status": "completed",
            "created_at": created_at,
            "prompt": prompt,
            "action_items": action_items,
            "overall_risk_assessment": risks,
            "agent_reports": agent_reports,
        }
    )


def test_dashboard_empty_when_no_decisions(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json() == {
        "total_decisions": 0,
        "distinct_prompts": 0,
        "total_action_items": 0,
        "high_priority_actions": 0,
        "top_risks": [],
        "agent_alignment": {},
        "per_month": [],
        "most_recent": "",
    }


def test_dashboard_aggregates_across_decisions(client):
    _put_decision(
        "run-1",
        "Expand into APAC",
        "2026-06-01T00:00:00.000Z",
        action_items=[{"priority": "HIGH", "task": "Hire lead"}, {"priority": "LOW", "task": "Update deck"}],
        risks=["Currency exposure", "Regulatory delay"],
        agent_reports={"ceo": {"alignment_score": Decimal("0.8")}, "cfo": {"alignment_score": Decimal("0.6")}},
    )
    _put_decision(
        "run-2",
        "Expand into APAC",  # duplicate prompt on purpose
        "2026-07-15T00:00:00.000Z",
        action_items=[{"priority": "HIGH", "task": "Sign lease"}],
        risks=["Currency exposure"],
        agent_reports={"ceo": {"alignment_score": Decimal("0.9")}},
    )

    response = client.get("/dashboard")
    assert response.status_code == 200
    body = response.json()

    assert body["total_decisions"] == 2
    assert body["distinct_prompts"] == 1
    assert body["total_action_items"] == 3
    assert body["high_priority_actions"] == 2
    assert body["top_risks"][0] == {"text": "currency exposure", "count": 2}
    assert body["agent_alignment"]["ceo"] == {"mean": 0.85, "samples": 2}
    assert body["agent_alignment"]["cfo"] == {"mean": 0.6, "samples": 1}
    assert body["per_month"] == [
        {"month": "2026-07", "count": 1},
        {"month": "2026-06", "count": 1},
    ]
    assert body["most_recent"] == "2026-07-15T00:00:00.000Z"
