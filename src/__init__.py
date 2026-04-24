"""OpenExec - Executive Board Simulation."""

__version__ = "0.1.0"

from .orchestrator import BaseOrchestrator
from .agents.interface import AgentReport
from .agents import AgentRegistry

__all__ = ["BaseOrchestrator", "AgentRegistry", "AgentReport"]
