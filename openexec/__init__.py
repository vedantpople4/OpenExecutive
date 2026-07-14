"""OpenExec - Executive Board Simulation."""

__version__ = "0.1.0"

from .orchestrator import Orchestrator
from .agents.interface import AgentReport
from .agents import AgentRegistry
from .cli import main

__all__ = ["Orchestrator", "AgentRegistry", "AgentReport", "main"]
