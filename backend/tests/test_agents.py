from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_agents_returns_four_cxos():
    response = client.get("/agents")
    assert response.status_code == 200
    body = response.json()
    assert {a["name"] for a in body} == {"ceo", "cfo", "cto", "cmo"}
    assert all(a["hasSystemPrompt"] for a in body)


def test_get_teams_matches_team_structure_shape():
    response = client.get("/teams")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"ceo", "cfo", "cto", "cmo"}
    assert body["cfo"] == [
        {"name": "financial_analyst", "parentCXO": "cfo"},
        {"name": "budget_planner", "parentCXO": "cfo"},
        {"name": "risk_analyst", "parentCXO": "cfo"},
    ]


def test_get_agent_prompt_known_agent():
    response = client.get("/agents/ceo/prompt")
    assert response.status_code == 200
    body = response.json()
    assert "prompt" in body
    assert len(body["prompt"]) > 0


def test_get_agent_prompt_unknown_agent_returns_404():
    response = client.get("/agents/not-a-real-agent/prompt")
    assert response.status_code == 404
