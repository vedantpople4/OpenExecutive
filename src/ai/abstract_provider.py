from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

class BaseProvider(ABC):
    """Abstract base class defining the interface for all LLM providers."""

    def __init__(self, ai_config: Dict[str, Any]):
        self.ai_config = ai_config
        # Basic validation should occur here if necessary (e.g., checking required API keys/endpoints)
        pass

    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Completes a general prompt and returns raw text."""
        pass

    @abstractmethod
    def complete_json(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Completes a prompt and reliably parses the response into a dictionary."""
        pass

    @abstractmethod
    def complete_json_with_retry(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None, max_attempts: int = 2) -> Dict[str, Any]:
        """Attempts to complete JSON parsing with a controlled retry loop for increased reliability."""
        pass