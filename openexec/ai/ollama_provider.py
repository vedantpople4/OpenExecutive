from openexec.ai.json_utils import JSONPipeline
from openexec.ai.prompts_constants import _CORRECTION_SYSTEM, _CORRECTION_USER
import requests
import json
import re
from typing import Any, Dict, Optional


class OllamaProvider:
    """Provider for Ollama-compatible LLMs (e.g., Ollama with local models like llama3, gemma, etc.).

    This provider uses the Ollama API at the local machine (default: http://localhost:11434)."""

    def __init__(self, ai_config: Dict[str, Any]):
        self.ai_config = ai_config
        self.base_url = ai_config.get("base_url", "http://localhost:11434")
        self.base_url = self.base_url.rstrip('/')
        self._pipeline = JSONPipeline()

    def complete(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Complete a prompt using the OpenAI-compatible API (LM Studio, Ollama with API compat, etc.)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # A runtime temperature_override (e.g. from `openexec run --temperature`)
        # beats the per-call value — agents hardcode temperature at every call
        # site, so the provider is the only choke point where an override can win.
        temperature_override = self.ai_config.get("temperature_override")
        if temperature_override is not None:
            resolved_temperature = temperature_override
        elif temperature is not None:
            resolved_temperature = temperature
        else:
            resolved_temperature = self.ai_config.get("temperature", 0.7)

        payload = {
            "model": self.ai_config.get("model", "llama3"),
            "messages": messages,
            "max_tokens": max_tokens if max_tokens is not None else self.ai_config.get("max_tokens", 4096),
            "temperature": resolved_temperature,
        }
        if self.ai_config.get("seed") is not None:
            payload["seed"] = int(self.ai_config["seed"])

        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = self.ai_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        max_retries = self.ai_config.get("max_retries", 2)
        timeout = self.ai_config.get("timeout", 120)
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    url, json=payload, headers=headers,
                    timeout=timeout
                )
                response.raise_for_status()
                result = response.json()
                message = result["choices"][0]["message"]
                content = message.get("content") or message.get("reasoning_content", "")
                return content
            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < max_retries:
                    wait = 2 ** attempt
                    import time
                    time.sleep(wait)
                    continue
                break
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"LLM API call failed: {e}")
        raise RuntimeError(f"LLM API timed out after {max_retries + 1} attempts (timeout={timeout}s each). Consider using a faster model or increasing timeout.")

    def complete_json(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Complete a prompt and parse the response as JSON."""
        # Suppress extended thinking for models like Gemma that output reasoning
        no_thinking_suffix = "\n\nIMPORTANT: Respond immediately with JSON only. No explanations, no thinking process, no markdown fences. Return ONLY valid JSON."
        if system_prompt:
            system_prompt = system_prompt + no_thinking_suffix
        else:
            system_prompt = "You are a helpful assistant. Respond immediately with JSON only. No explanations, no thinking process, no markdown fences. Return ONLY valid JSON."

        raw_response = self.complete(
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

    def complete_json_with_retry(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None, max_attempts: int = 2) -> Dict[str, Any]:
        """Complete a prompt with retry logic for JSON extraction."""
        no_thinking_suffix = "\n\nIMPORTANT: Output your response as valid JSON only. Do not wrap it in markdown code fences. Do not include any text outside the JSON object. Respond immediately with no thinking."

        # Suppress extended thinking
        if system_prompt:
            system_prompt = system_prompt + no_thinking_suffix
        else:
            system_prompt = "Respond immediately with JSON only. No explanations, no thinking process, no markdown fences."

        enhanced_prompt = prompt + "\n\nIMPORTANT: Output your response as valid JSON only. Do not wrap it in markdown code fences. Do not include any text outside the JSON object."
        raw_response = self.complete(
            prompt=enhanced_prompt,
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
        user_prompt = _CORRECTION_USER.format(broken_text=broken_text[:1500])

        messages = [{"role": "user", "content": user_prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": _CORRECTION_SYSTEM})
        else:
            messages.insert(0, {"role": "system", "content": _CORRECTION_SYSTEM})

        payload = {
            "model": self.ai_config.get("model", "llama3"),
            "messages": messages,
            "max_tokens": self.ai_config.get("max_tokens", 4096),
            "temperature": 0.0,  # Use 0 temp for correction — deterministic
        }
        if self.ai_config.get("seed") is not None:
            payload["seed"] = int(self.ai_config["seed"])

        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = self.ai_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = requests.post(
                url, json=payload, headers=headers,
                timeout=self.ai_config.get("timeout", 120)
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            # Strip fences from corrected response too
            content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```\s*$', '', content)
            return content.strip()
        except Exception:
            # Self-correction failed — return original for caller to retry
            return broken_text
