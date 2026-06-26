from openexec.ai.json_utils import JSONPipeline
from openexec.ai.prompts_constants import _CORRECTION_SYSTEM, _CORRECTION_USER
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional


class AIClient:
    """Wrapper for LLM API calls using an abstract provider pattern.

    The client manages the 4-layer JSON robustness pipeline, delegating raw API
    calls to a configured BaseProvider instance.
    """

    def __init__(self, provider: Any | None = None, settings_path: str | None = None):
        if provider is not None:
            self.provider = provider
        else:
            from openexec.ai.ollama_provider import OllamaProvider
            settings = self._load_settings(settings_path)
            ai_config = settings.get("ai", {})
            self.provider = OllamaProvider(ai_config)
        self._pipeline = JSONPipeline()

    def _load_settings(self, settings_path: str | None = None) -> Dict[str, Any]:
        if settings_path is None:
            settings_path = "settings.json"
        path = Path(settings_path)
        if not path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")
        with open(path) as f:
            return json.load(f)

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Delegates completion to the configured provider."""
        return self.provider.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def complete_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Dict[str, Any]:
        """Delegates JSON completion to the configured provider and runs parsing."""
        raw_response = self.provider.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return self._pipeline.parse(
            raw_response,
            system_prompt=system_prompt,
            correct_fn=self._self_correct,
        )

    def complete_json_with_retry(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """Delegates JSON completion with explicit retry control."""
        raw_response = self.provider.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return self._pipeline.parse(
            raw_response,
            system_prompt=system_prompt,
            max_correction_attempts=max_attempts - 1,
            correct_fn=self._self_correct,
        )

    def _self_correct(
        self,
        broken_text: str,
        system_prompt: str | None = None,
    ) -> str:
        import requests

        user_prompt = _CORRECTION_USER.format(broken_text=broken_text[:1500])

        messages = [{"role": "user", "content": user_prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": _CORRECTION_SYSTEM})
        else:
            messages.insert(0, {"role": "system", "content": _CORRECTION_SYSTEM})

        payload = {
            "model": self.provider.ai_config.get("model", "llama3"),
            "messages": messages,
            "max_tokens": self.provider.ai_config.get("max_tokens", 4096),
            "temperature": 0.0,
        }

        url = f"{self.provider.ai_config['base_url'].rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = self.provider.ai_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = requests.post(
                url, json=payload, headers=headers,
                timeout=self.provider.ai_config.get("timeout", 120)
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            result = re.sub(r'^```(?:json)?\s*', '', result, flags=re.MULTILINE)
            result = re.sub(r'\s*```\s*$', '', result)
            return result.strip()
        except Exception:
            return broken_text
