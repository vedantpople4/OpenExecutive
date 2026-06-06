import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openexec.events import (
    Event, EventType, SimulationInitialized, InceptionStarted,
    InceptionCompleted, AnalysisStarted, AgentReportGenerated,
    AnalysisCompleted, DeliberationStarted, DeliberationRoundStarted,
    DeliberationRoundCompleted, DeliberationCompleted, SynthesisStarted,
    SynthesisCompleted, ErrorOccurred
)


class EventStore:
    """Manages event storage, retrieval, and state reconstruction.

    Implements an append-only event store pattern for the simulation system.
    Events are stored to disk for auditability and can be replayed to reconstruct state.
    """

    def __init__(self, storage_path: str = "memory/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.events: List[Event] = []
        self._event_classes = {
            EventType.SIMULATION_INITIALIZED: SimulationInitialized,
            EventType.INCEPTION_STARTED: InceptionStarted,
            EventType.INCEPTION_COMPLETED: InceptionCompleted,
            EventType.ANALYSIS_STARTED: AnalysisStarted,
            EventType.AGENT_REPORT_GENERATED: AgentReportGenerated,
            EventType.ANALYSIS_COMPLETED: AnalysisCompleted,
            EventType.DELIBERATION_STARTED: DeliberationStarted,
            EventType.DELIBERATION_ROUND_STARTED: DeliberationRoundStarted,
            EventType.DELIBERATION_ROUND_COMPLETED: DeliberationRoundCompleted,
            EventType.DELIBERATION_COMPLETED: DeliberationCompleted,
            EventType.SYNTHESIS_STARTED: SynthesisStarted,
            EventType.SYNTHESIS_COMPLETED: SynthesisCompleted,
            EventType.ERROR_OCCURRED: ErrorOccurred,
        }

    def append(self, event: Event) -> str:
        """Append an event to the store and persist to disk.

        Args:
            event: The event to append

        Returns:
            The event_id of the appended event
        """
        if not event.event_id:
            event.event_id = str(uuid.uuid4())

        self.events.append(event)
        self._persist_event(event)
        return event.event_id

    def _persist_event(self, event: Event) -> None:
        """Persist an event to disk as JSON."""
        timestamp_str = event.timestamp.isoformat()
        event_data = {
            "event_id": event.event_id,
            "timestamp": timestamp_str,
            "aggregate_id": event.aggregate_id,
            "event_type": event.event_type.value,
            **{k: v for k, v in self._extract_event_data(event).items() if v is not None}
        }

        filename = f"{event.event_id}.json"
        filepath = self.storage_path / filename
        with open(filepath, 'w') as f:
            json.dump(event_data, f, indent=2, default=str)

    def _extract_event_data(self, event: Event) -> Dict[str, Any]:
        """Extract relevant data from an event for serialization."""
        result = {}
        for key, value in event.__dict__.items():
            if key in ('event_id', 'timestamp', 'event_type', 'aggregate_id'):
                continue
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def get_events(self, aggregate_id: Optional[str] = None) -> List[Event]:
        """Retrieve all events, optionally filtered by aggregate_id.

        Args:
            aggregate_id: If provided, only return events for this simulation

        Returns:
            List of events in chronological order
        """
        if not aggregate_id:
            return list(self.events)

        return [e for e in self.events if e.aggregate_id == aggregate_id]

    def replay(self, aggregate_id: str) -> Dict[str, Any]:
        """Replay events to reconstruct the state of a simulation.

        Args:
            aggregate_id: The simulation ID to reconstruct state for

        Returns:
            A dictionary representing the reconstructed state
        """
        events = self.get_events(aggregate_id)
        if not events:
            return {}

        state = {
            "simulation_id": aggregate_id,
            "status": "idle",
            "phase": "",
            "agent_outputs": {},
            "deliberation_outputs": {},
            "errors": [],
        }

        for event in events:
            state = self._apply_event_to_state(event, state)

        return state

    def _apply_event_to_state(self, event: Event, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single event to a state dictionary.

        Args:
            event: The event to apply
            state: The current state dict

        Returns:
            The updated state dict
        """
        if event.event_type == EventType.SIMULATION_INITIALIZED:
            if isinstance(event, SimulationInitialized):
                state["core_prompt"] = event.core_prompt
                state["decision_point"] = event.decision_point
                state["status"] = "initialized"
        elif event.event_type == EventType.INCEPTION_STARTED:
            state["phase"] = "inception"
            state["status"] = "analyzing"
        elif event.event_type == EventType.INCEPTION_COMPLETED:
            if isinstance(event, InceptionCompleted) and event.ceo_report:
                state["agent_outputs"]["ceo"] = event.ceo_report
        elif event.event_type == EventType.ANALYSIS_STARTED:
            state["phase"] = "analysis"
        elif event.event_type == EventType.AGENT_REPORT_GENERATED:
            if isinstance(event, AgentReportGenerated):
                state["agent_outputs"][event.agent_name] = event.report_data
        elif event.event_type == EventType.ANALYSIS_COMPLETED:
            state["status"] = "reviewing"
        elif event.event_type == EventType.DELIBERATION_STARTED:
            state["phase"] = "deliberation"
        elif event.event_type == EventType.DELIBERATION_ROUND_COMPLETED:
            if isinstance(event, DeliberationRoundCompleted):
                state["deliberation_outputs"][event.round_number] = event.reports
        elif event.event_type == EventType.DELIBERATION_COMPLETED:
            state["status"] = "synthesizing"
        elif event.event_type == EventType.SYNTHESIS_STARTED:
            state["phase"] = "synthesis"
        elif event.event_type == EventType.SYNTHESIS_COMPLETED:
            state["status"] = "complete"
        elif event.event_type == EventType.ERROR_OCCURRED:
            if isinstance(event, ErrorOccurred):
                state["errors"].append({
                    "phase": event.phase,
                    "message": event.error_message,
                    "timestamp": event.timestamp.isoformat()
                })

        return state

    def load_from_disk(self, aggregate_id: str) -> List[Event]:
        """Load all events for an aggregate from disk.

        Args:
            aggregate_id: The simulation ID to load events for

        Returns:
            List of loaded events
        """
        loaded_events = []
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    event_data = json.load(f)

                if event_data.get("aggregate_id") != aggregate_id:
                    continue

                event_type_str = event_data.get("event_type")
                event_type = EventType(event_type_str)
                event_class = self._event_classes.get(event_type)

                if event_class:
                    event = event_class(**event_data)
                    loaded_events.append(event)
            except Exception:
                continue

        loaded_events.sort(key=lambda e: e.timestamp)
        return loaded_events

    def clear(self, aggregate_id: Optional[str] = None) -> None:
        """Clear events from the store.

        Args:
            aggregate_id: If provided, only clear events for this simulation.
                          Otherwise, clear all events.
        """
        if aggregate_id:
            self.events = [e for e in self.events if e.aggregate_id != aggregate_id]
            for filepath in self.storage_path.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        if json.load(f).get("aggregate_id") == aggregate_id:
                            filepath.unlink()
                except Exception:
                    continue
        else:
            self.events = []
            for filepath in self.storage_path.glob("*.json"):
                filepath.unlink()