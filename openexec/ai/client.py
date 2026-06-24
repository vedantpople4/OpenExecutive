from openexec.ai.abstract_provider import BaseProvider
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from openexec.ai.prompts_constants import _CORRECTION_SYSTEM, _CORRECTION_USER


class AIClient:
    """Wrapper for LLM API calls using an abstract provider pattern.

    The client manages the 4-layer JSON robustness pipeline, delegating raw API
    calls to a configured BaseProvider instance.
    """

    def __init__(self, provider: BaseProvider | None = None, settings_path: str | None = None):
        if provider is not None:
            self.provider = provider
        else:
            from openexec.ai.ollama_provider import OllamaProvider
            settings = self._load_settings(settings_path)
            ai_config = settings.get("ai", {})
            self.provider = OllamaProvider(ai_config)
        self._json5 = None

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
        return self._parse_with_pipeline(raw_response, system_prompt=system_prompt)

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
        return self._parse_with_pipeline(
            raw_response, 
            system_prompt=system_prompt, 
            max_correction_attempts=max_attempts - 1
        )

    def _parse_with_pipeline(
        self,
        raw_text: str,
        system_prompt: str | None = None,
        max_correction_attempts: int = 1,
    ) -> Dict[str, Any]:
        text = self._preprocess(raw_text)
        fixed = self._apply_structural_fixes(text)
        parsed = self._attempt_parse(fixed)
        if parsed is not None:
            return parsed

        parsed = self._try_json5(fixed)
        if parsed is not None:
            return parsed

        broken = fixed
        for attempt in range(max_correction_attempts):
            corrected_text = self._self_correct(broken, system_prompt=system_prompt)
            corrected_clean = self._preprocess(corrected_text)
            corrected_fixed = self._apply_structural_fixes(corrected_clean)
            parsed = self._attempt_parse(corrected_fixed)
            if parsed is not None:
                return parsed
            parsed = self._try_json5(corrected_fixed)
            if parsed is not None:
                return parsed
            broken = corrected_fixed

        raise ValueError(
            f"Failed to parse LLM response as JSON after 4 layers.\n"
            f"Original (first 300 chars): {raw_text[:300]}\n"
            f"Last attempted (first 300 chars): {broken[:300]}"
        )

    def _preprocess(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text)

        start = -1
        for i, ch in enumerate(text):
            if ch in ('{', '['):
                start = i
                break

        if start >= 0:
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch in ('{', '['):
                    depth += 1
                elif ch in ('}', ']'):
                    depth -= 1
                    if depth == 0:
                        text = text[start:i+1]
                        break

        text = text.replace('\ufeff', '').replace('\x00', '')
        text = text.replace('\r', '\\r')
        text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f]', '', text)

        return text.strip()

    def _apply_structural_fixes(self, text: str) -> str:
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        fixed = []
        in_string = False
        escape_next = False
        for ch in text:
            if escape_next:
                fixed.append(ch)
                escape_next = False
                continue
            if ch == '\\':
                fixed.append(ch)
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                fixed.append(ch)
            elif ch == '\n' and in_string:
                fixed.append('\\n')
            elif ch == '\r' and in_string:
                fixed.append('\\r')
            else:
                fixed.append(ch)

        text = ''.join(fixed)

        def fix_unquoted_key(m):
            key = m.group(1)
            return f'"{key}":'
        text = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*)\s*:(\s*[{"\[])', fix_unquoted_key, text)

        return text

    def _attempt_parse(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @property
    def _json5_module(self):
        if self._json5 is None:
            try:
                import json5 as j5
                self._json5 = j5
            except ImportError:
                self._json5 = False
        return self._json5

    def _try_json5(self, text: str) -> Optional[Dict[str, Any]]:
        j5 = self._json5_module
        if not j5:
            return None
        try:
            return j5.loads(text)
        except Exception:
            return None

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
            response = self.provider.requests.post(
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