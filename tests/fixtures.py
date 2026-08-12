"""Shared sample results dict matching the orchestrator's output shape.

Used by renderer, risk, and export tests so the "real artifact" code paths are
exercised against a realistic payload, not an invented minimal stub.
"""


def sample_results():
    """A complete simulation results dict, mirroring orchestrator output."""
    return {
        "simulation_id": "demo-sim",
        "executive_summary": "Commit to the integration path for Q2 revenue.",
        "decision_point": "Decision required for: Should we hire?",
        "fallback_warnings": ["cfo (round 2): AI call failed, stub used"],
        "board_decision": {
            "summary": "We commit to the integration path.",
            "consensus_points": ["Growth first", "Manage burn"],
            "dissent_points": ["Hire senior only"],
            "final_priority_actions": ["Post reqs now"],
            "dissenting_opinions": ["CTO wants depth first"],
            "contingencies": ["If burn exceeds 20%, freeze hiring"],
        },
        "deliberation_rounds": {
            "1": {
                "ceo": {
                    "summary": "Frame the debate",
                    "round_number": 1,
                    "agreements": ["Growth matters"],
                    "conflicts": ["Speed vs depth"],
                    "required_changes": ["None"],
                }
            }
        },
        "synthesized_recommendations": [
            "[CEO] Post two job reqs",
            "[CFO] Cut one vendor",
        ],
        "overall_risk_assessment": [
            "[CFO] Burn risk high with probability: High",
            "[CTO] Scaling risk late",
        ],
        "agent_reports": {
            "ceo": {
                "title": "Growth analysis",
                "summary": "We must grow revenue to $2m by Q2.",
                "key_findings": ["Team is thin at 5 engineers"],
                "recommendations": ["Hire two engineers"],
                "risks": ["Burn rate rising 20%"],
                "alignment_score": 0.8,
                "is_fallback": False,
                "grounding": {"claims_checked": 3, "claims_grounded": 2, "ungrounded": ["$2m"]},
            },
            "cfo": {
                "title": "Budget analysis",
                "summary": "Costs are 15% higher than plan.",
                "key_findings": [],
                "recommendations": [],
                "risks": [],
                "alignment_score": 0.9,
                "is_fallback": False,
                "grounding": None,
            },
            "cto": {
                "title": "Failed analysis",
                "summary": "stub",
                "key_findings": [],
                "recommendations": [],
                "risks": [],
                "alignment_score": 0.0,
                "is_fallback": True,
                "grounding": None,
            },
        },
        "data_sources": {
            "timestamp": "2026-08-01T00:00:00",
            "access_success_rate": 0.9,
            "sources_accessed": ["data/company_background.md"],
            "sources_failed": [],
            "all_available_sources": ["data/company_background.md"],
            "research_sources_consulted": ["example.com"],
        },
    }
