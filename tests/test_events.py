"""Tests for openexec/events.py — the event contract shared with the frontend."""

import dataclasses

from openexec.events import (
    AgentSpeaking,
    EventType,
    SpecialistReportGenerated,
    TeamAnalysisCompleted,
    TeamAnalysisStarted,
)


class TestTeamAndSpeakingEvents:
    """The four event types the frontend renders but the engine never emitted.
    Their `type` strings are a wire contract with frontend/src/api/types.ts —
    a typo here silently produces an event the UI ignores."""

    def test_wire_strings_match_the_frontend_union(self):
        assert EventType.TEAM_ANALYSIS_STARTED.value == "team_analysis_started"
        assert EventType.SPECIALIST_REPORT_GENERATED.value == "specialist_report_generated"
        assert EventType.TEAM_ANALYSIS_COMPLETED.value == "team_analysis_completed"
        assert EventType.AGENT_SPEAKING.value == "agent_speaking"

    def test_constructible_with_only_an_event_id(self):
        for cls in (TeamAnalysisStarted, TeamAnalysisCompleted, AgentSpeaking,
                    SpecialistReportGenerated):
            event = cls(event_id="e1")
            assert event.aggregate_id == ""

    def test_agent_speaking_carries_no_round_number(self):
        """asdict would emit round_number=None, and the frontend's guard is
        `!== undefined` — null takes the round branch and misroutes the event
        to a deliberation round that does not exist yet."""
        assert "round_number" not in dataclasses.asdict(AgentSpeaking(event_id="e1"))
