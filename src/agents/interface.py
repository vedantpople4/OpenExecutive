from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentReport:
    """Standard report format for agent insights."""

    title: str
    summary: str
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    confidence_score: float = 0.5  # 0.0 to 1.0
    reasoning: dict[str, Any] = field(default_factory=dict)
