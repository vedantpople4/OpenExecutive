from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class EventType(str, Enum):
    SIMULATION_INITIALIZED = "simulation_initialized"
    INCEPTION_STARTED = "inception_started"
    INCEPTION_COMPLETED = "inception_completed"
    ANALYSIS_STARTED = "analysis_started"
    AGENT_REPORT_GENERATED = "agent_report_generated"
    ANALYSIS_COMPLETED = "analysis_completed"
    DELIBERATION_STARTED = "deliberation_started"
    DELIBERATION_ROUND_STARTED = "deliberation_round_started"
    DELIBERATION_ROUND_COMPLETED = "deliberation_round_completed"
    DELIBERATION_COMPLETED = "deliberation_completed"
    SYNTHESIS_STARTED = "synthesis_started"
    SYNTHESIS_COMPLETED = "synthesis_completed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """Base class for all simulation events."""
    event_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: str = ""  # Links to simulation instance
    event_type: EventType = EventType.SIMULATION_INITIALIZED


@dataclass
class SimulationInitialized(Event):
    """Event emitted when a simulation is initialized."""
    event_type: EventType = EventType.SIMULATION_INITIALIZED
    core_prompt: str = ""
    decision_point: Optional[str] = None
    agent_names: list[str] = field(default_factory=list)


@dataclass
class InceptionStarted(Event):
    """Event emitted when Phase 1 (Inception) starts."""
    event_type: EventType = EventType.INCEPTION_STARTED


@dataclass
class InceptionCompleted(Event):
    """Event emitted when Phase 1 (Inception) completes."""
    event_type: EventType = EventType.INCEPTION_COMPLETED
    ceo_report: Optional[dict] = None


@dataclass
class AnalysisStarted(Event):
    """Event emitted when Phase 2 (Analysis) starts."""
    event_type: EventType = EventType.ANALYSIS_STARTED


@dataclass
class AgentReportGenerated(Event):
    """Event emitted when an agent generates a report."""
    event_type: EventType = EventType.AGENT_REPORT_GENERATED
    agent_name: str = ""
    report_data: Optional[dict] = None


@dataclass
class AnalysisCompleted(Event):
    """Event emitted when Phase 2 (Analysis) completes."""
    event_type: EventType = EventType.ANALYSIS_COMPLETED
    reports_generated: list[str] = field(default_factory=list)


@dataclass
class DeliberationStarted(Event):
    """Event emitted when Phase 3 (Deliberation) starts."""
    event_type: EventType = EventType.DELIBERATION_STARTED


@dataclass
class DeliberationRoundStarted(Event):
    """Event emitted when a deliberation round starts."""
    event_type: EventType = EventType.DELIBERATION_ROUND_STARTED
    round_number: int = 0


@dataclass
class DeliberationRoundCompleted(Event):
    """Event emitted when a deliberation round completes."""
    event_type: EventType = EventType.DELIBERATION_ROUND_COMPLETED
    round_number: int = 0
    reports: dict = field(default_factory=dict)


@dataclass
class DeliberationCompleted(Event):
    """Event emitted when Phase 3 (Deliberation) completes."""
    event_type: EventType = EventType.DELIBERATION_COMPLETED
    total_rounds: int = 0


@dataclass
class SynthesisStarted(Event):
    """Event emitted when Phase 4 (Synthesis) starts."""
    event_type: EventType = EventType.SYNTHESIS_STARTED


@dataclass
class SynthesisCompleted(Event):
    """Event emitted when Phase 4 (Synthesis) completes."""
    event_type: EventType = EventType.SYNTHESIS_COMPLETED
    final_report: Optional[dict] = None


@dataclass
class ErrorOccurred(Event):
    """Event emitted when an error occurs during simulation."""
    event_type: EventType = EventType.ERROR_OCCURRED
    error_message: str = ""
    phase: str = ""