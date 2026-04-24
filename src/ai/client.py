"""LLM Client Wrapper for OpenExec - OpenAI Compatible Format."""

import os
import json
from typing import Any, Dict
from pathlib import Path


class AIClient:
    """Wrapper for LLM API calls using OpenAI-compatible format.

    Supports:
    - Local LLMs (Ollama, vLLM, etc.)
    - OpenAI models
    - Anthropic models (via OpenAI-compatible endpoint)
    - Any OpenAI-compatible API
    """

    def __init__(self, settings_path: str | None = None):
        """Initialize the AI client.

        Args:
            settings_path: Path to settings.json file. If None, looks for settings.json in current directory.
        """
        self.settings = self._load_settings(settings_path)
        self.ai_config = self.settings.get("ai", {})

        # Validate required settings
        if not self.ai_config.get("base_url"):
            raise ValueError("base_url not found in settings.json")

        # Import requests for HTTP calls
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError(
                "requests package not installed. Install with: pip install requests"
            )

    def _load_settings(self, settings_path: str | None = None) -> Dict[str, Any]:
        """Load settings from JSON file.

        Args:
            settings_path: Path to settings.json file.

        Returns:
            Dictionary containing settings.
        """
        if settings_path is None:
            # Look for settings.json in current directory
            settings_path = "settings.json"

        path = Path(settings_path)
        if not path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        with open(path, 'r') as f:
            return json.load(f)

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Complete a prompt using the LLM (OpenAI-compatible format).

        Args:
            prompt: The user prompt to complete.
            system_prompt: Optional system prompt for persona/context.
            max_tokens: Maximum tokens in response (overrides settings).
            temperature: Sampling temperature (overrides settings).

        Returns:
            The LLM response text.
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request payload
        payload = {
            "model": self.ai_config.get("model", "llama3"),
            "messages": messages,
            "max_tokens": max_tokens or self.ai_config.get("max_tokens", 4096),
            "temperature": temperature if temperature is not None else self.ai_config.get("temperature", 0.7),
        }

        # Make API call
        url = f"{self.ai_config['base_url'].rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}

        # Add API key if provided (not needed for local models)
        api_key = self.ai_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = self.requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.ai_config.get("timeout", 120)
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except self.requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    def complete_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Dict[str, Any]:
        """Complete a prompt and parse response as JSON.

        Args:
            prompt: The user prompt to complete.
            system_prompt: Optional system prompt for persona/context.
            max_tokens: Maximum tokens in response (overrides settings).
            temperature: Sampling temperature (overrides settings).

        Returns:
            Parsed JSON response as dictionary.
        """
        # Add JSON formatting instruction to prompt
        json_instruction = "\n\nIMPORTANT: Output your response as valid JSON only, with no additional text or markdown formatting."
        enhanced_prompt = prompt + json_instruction

        response_text = self.complete(
            prompt=enhanced_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Clean up response if it has markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text}")
