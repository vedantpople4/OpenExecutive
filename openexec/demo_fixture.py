"""Canned results for `openexec demo` — a realistic run with no LLM.

Mirrors the exact shape the orchestrator produces (see openexec/orchestrator.py's
final_report building) so the demo exercises the real renderers, not a stub.
Used only by the demo path.
"""


def demo_results():
    """A complete, realistic simulation result dict for demo rendering."""
    return {
        "executive_summary": (
            "The board commits to the integration path as the primary strategy "
            "to secure immediate revenue and protect runway, accepting controlled "
            "technical debt for speed to market."
        ),
        "decision_point": "Decision required for: Should we build an internal platform or integrate with a partner?",
        "board_decision": {
            "summary": "Commit to the integration path for Q2 revenue, with a shared platform roadmap to revisit architecture in Q4.",
            "consensus_points": [
                "Immediate revenue traction via the Integration path is mandatory for Q2 targets.",
                "Runway protection and immediate financial viability take precedence over long-term architectural purity.",
                "Partnership depth must be validated through a 30-day pilot before full commitment.",
            ],
            "dissent_points": [
                "CTO vs. CFO conflict over integration speed vs. long-term technical debt.",
            ],
            "final_priority_actions": [
                "Launch a partnership pilot with the top two integration candidates within 30 days.",
                "Freeze internal platform build until pilot results land.",
            ],
            "dissenting_opinions": [
                "CTO argues the internal platform is defensible IP; CFO counters it burns runway with no revenue.",
            ],
            "contingencies": [
                "If pilot adoption < 40%, revisit the internal-platform build as a hedge.",
            ],
        },
        "deliberation_rounds": {
            "1": {
                "ceo": {
                    "summary": "The CEO frames the core conflict: revenue now (CFO) vs. architecture later (CTO).",
                    "round_number": 1,
                    "agreements": ["Either path requires focus"],
                    "conflicts": ["Speed to market vs. long-term leverage"],
                }
            },
            "2": {
                "cfo": {
                    "summary": "CFO models integration at 60% lower upfront cost with revenue in Q2.",
                    "round_number": 2,
                    "agreements": ["Revenue timing matters most"],
                    "conflicts": ["CTO's cost estimate is optimistic"],
                },
                "cto": {
                    "summary": "CTO warns of rework cost within 18 months if the integration wins.",
                    "round_number": 2,
                },
            },
            "5": {
                "ceo": {
                    "summary": "CEO synthesizes: integrate now, keep platform option alive via pilot gates.",
                    "round_number": 5,
                }
            },
        },
        "agent_reports": {
            "ceo": {
                "title": "Strategy Analysis: Stakeholder Alignment",
                "summary": "The decision splits the board along time horizon: near-term revenue vs. long-term leverage.",
                "key_findings": [
                    "Revenue timing is the dominant driver in the current runway position.",
                    "The team can execute integration faster than an internal build.",
                ],
                "recommendations": [
                    "Back the pilot-first integration approach.",
                    "Maintain a Q4 architecture review checkpoint.",
                ],
                "risks": [
                    "Hedging between paths dilutes execution.",
                ],
                "alignment_score": 0.82,
                "is_fallback": False,
                "grounding": {"claims_checked": 4, "claims_grounded": 3, "ungrounded": ["60%"]},
            },
            "cfo": {
                "title": "Financial Analysis: Runway and Revenue",
                "summary": "Integration preserves runway and targets revenue within one quarter.",
                "key_findings": [
                    "Integration reduces near-term capital outlay by an estimated 60%.",
                ],
                "recommendations": [
                    "Approve a 30-day pilot with cost caps.",
                ],
                "risks": [
                    "Partner pricing uncertainty could erode margin.",
                ],
                "alignment_score": 0.9,
                "is_fallback": False,
                "grounding": {"claims_checked": 3, "claims_grounded": 2, "ungrounded": ["60%"]},
            },
            "cto": {
                "title": "Technical Analysis: Build vs. Integrate",
                "summary": "Integration accelerates delivery but shifts control to the partner.",
                "key_findings": [
                    "Integration reuses proven capabilities, cutting engineering time.",
                ],
                "recommendations": [
                    "Protect a core chokepoint in-house regardless of path.",
                ],
                "risks": [
                    "Partner lock-in could archive rework within 18 months.",
                ],
                "alignment_score": 0.72,
                "is_fallback": False,
                "grounding": {"claims_checked": 2, "claims_grounded": 1, "ungrounded": ["18 months"]},
            },
            "cmo": {
                "title": "Market Analysis: Go-to-Market",
                "summary": "The market rewards speed; integration shortens time-to-value for customers.",
                "key_findings": [
                    "Early customers prioritize time-to-value over architecture.",
                ],
                "recommendations": [
                    "Lead the launch with the integration value story.",
                ],
                "risks": [
                    "A thin integration story weakens positioning against deeper competitors.",
                ],
                "alignment_score": 0.78,
                "is_fallback": False,
                "grounding": {"claims_checked": 2, "claims_grounded": 2, "ungrounded": []},
            },
        },
        "synthesized_recommendations": [
            "[CEO] Approve a 30-day integration pilot with the top two candidates.",
            "[CFO] Cap pilot spend and model margin under partner pricing.",
            "[CTO] Keep the platform chokepoint in-house during the pilot.",
            "[CMO] Launch the integration value story to early customers.",
        ],
        "overall_risk_assessment": [
            "[CFO] Pilot underdelivers and burns runway with probability: High",
            "[CTO] Partner lock-in forces rework in 18 months",
            "[CMO] Integration story fails to differentiate",
            "[CEO] Decision paralysis splits focus",
        ],
        "data_sources": {
            "timestamp": "2026-08-10T12:00:00",
            "access_success_rate": 0.9,
            "sources_accessed": ["data/company_background.md", "data/current_infra.txt"],
            "research_sources_consulted": ["integrations marketplace (live search)"],
        },
    }