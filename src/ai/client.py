"""LLM Client Wrapper for OpenExec - OpenAI Compatible Format."""

import json
import re
from typing import Any, Dict, Optional

from pathlib import Path


# ----------------------------------------------------------------------
# Self-correction prompt used when all fixers fail (Layer 4)
# ----------------------------------------------------------------------
_CORRECTION_SYSTEM = (
    "You are a JSON correction assistant. Your output must be ONLY valid JSON "
    "— no markdown, no explanation, no commentary."
)

_CORRECTION_USER = (
    "The following text was supposed to be valid JSON but had errors. "
    "Fix all syntax errors and return ONLY the corrected JSON object.\n\n"
    "Broken input:\n{broken_text}\n\n"
    "Corrected JSON:"
)


class AIClient:
    """Wrapper for LLM API calls using OpenAI-compatible format.

    Supports:
    - Local LLMs (Ollama, vLLM, etc.)
    - OpenAI models
    - Anthropic models (via OpenAI-compatible endpoint)
    - Any OpenAI-compatible API

    JSON Robustness:
    Uses a 4-layer pipeline to extract valid JSON from LLM responses:
      Layer 1: Preprocess — strip fences, extract JSON span, remove invisible chars
      Layer 2: Structural fixes — unescaped newlines, trailing commas, unquoted keys
      Layer 3: Try json5 (relaxed JSON parser) as fallback
      Layer 4: LLM self-correction — one retry call back to the model
      If all fail: raise ValueError for caller to handle
    """

    def __init__(self, settings_path: str | None = None):
        self.settings = self._load_settings(settings_path)
        self.ai_config = self.settings.get("ai", {})

        if not self.ai_config.get("base_url"):
            raise ValueError("base_url not found in settings.json")

        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests package not installed. Install with: pip install requests")

        # Lazy-load json5 — not critical, only needed if Layer 2 fails
        self._json5 = None
        self._json5_available = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Complete a prompt using the LLM (OpenAI-compatible format)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.ai_config.get("model", "llama3"),
            "messages": messages,
            "max_tokens": max_tokens or self.ai_config.get("max_tokens", 4096),
            "temperature": temperature if temperature is not None else self.ai_config.get("temperature", 0.7),
        }

        url = f"{self.ai_config['base_url'].rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}

        api_key = self.ai_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = self.requests.post(
                url, json=payload, headers=headers,
                timeout=self.ai_config.get("timeout", 120)
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except self.requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    def complete_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Dict[str, Any]:
        """Complete a prompt and parse response as JSON, with 4-layer robustness.

        Uses a layered approach:
          1. Strip fences + extract JSON span + remove invisible chars
          2. Fix known structural issues (unescaped newlines, trailing commas, unquoted keys)
          3. Try json5.loads() if available
          4. LLM self-correction (one retry)
          If all fail: raise ValueError

        Args:
            prompt: The user prompt to complete.
            system_prompt: Optional system prompt for persona/context.
            max_tokens: Maximum tokens (overrides settings).
            temperature: Sampling temperature (overrides settings).

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            ValueError: When JSON cannot be extracted after all 4 layers.
        """
        json_instruction = (
            "\n\nIMPORTANT: Output your response as valid JSON only. "
            "Do not wrap it in markdown code fences. "
            "Do not include any text outside the JSON object."
        )
        enhanced_prompt = prompt + json_instruction

        raw_response = self.complete(
            prompt=enhanced_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Pass system_prompt so Layer 4 self-correction can reuse it
        return self._parse_with_pipeline(raw_response, system_prompt=system_prompt)

    def complete_json_with_retry(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """Same as complete_json but with explicit retry loop for callers who want control.

        Args:
            max_attempts: Maximum LLM calls (1 original + (max_attempts - 1) corrections).
                          Default 2 = one correction attempt before giving up.
        """
        json_instruction = (
            "\n\nIMPORTANT: Output your response as valid JSON only. "
            "Do not wrap it in markdown code fences. "
            "Do not include any text outside the JSON object."
        )
        enhanced_prompt = prompt + json_instruction

        raw_response = self.complete(
            prompt=enhanced_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return self._parse_with_pipeline(
            raw_response,
            system_prompt=system_prompt,
            max_correction_attempts=max_attempts - 1,
        )

    # ------------------------------------------------------------------
    # Layer pipeline
    # ------------------------------------------------------------------

    def _parse_with_pipeline(
        self,
        raw_text: str,
        system_prompt: str | None = None,
        max_correction_attempts: int = 1,
    ) -> Dict[str, Any]:
        """Run the 4-layer JSON extraction pipeline.

        Args:
            raw_text: Raw response text from LLM.
            system_prompt: System prompt used in original call (passed through to correction).
            max_correction_attempts: Number of self-correction retries allowed.

        Returns:
            Parsed JSON dict.

        Raises:
            ValueError: After all layers exhausted.
        """
        # Layer 1: preprocess
        text = self._preprocess(raw_text)

        # Layer 2: attempt standard parse with fixes
        fixed = self._apply_structural_fixes(text)
        parsed = self._attempt_parse(fixed)
        if parsed is not None:
            return parsed

        # Layer 3: try json5 (handles trailing commas, unquoted keys, JS comments)
        parsed = self._try_json5(fixed)
        if parsed is not None:
            return parsed

        # Layer 4: LLM self-correction (up to max_correction_attempts)
        broken = fixed
        for attempt in range(max_correction_attempts):
            corrected_text = self._self_correct(broken, system_prompt=system_prompt)
            # Re-run Layers 1-3 on the corrected text
            corrected_clean = self._preprocess(corrected_text)
            corrected_fixed = self._apply_structural_fixes(corrected_clean)
            parsed = self._attempt_parse(corrected_fixed)
            if parsed is not None:
                return parsed
            parsed = self._try_json5(corrected_fixed)
            if parsed is not None:
                return parsed
            # Update broken for next attempt
            broken = corrected_fixed

        # Exhausted all layers
        raise ValueError(
            f"Failed to parse LLM response as JSON after 4 layers.\n"
            f"Original (first 300 chars): {raw_text[:300]}\n"
            f"Last attempted (first 300 chars): {broken[:300]}"
        )

    # ------------------------------------------------------------------
    # Layer 1 helpers: preprocess
    # ------------------------------------------------------------------

    def _preprocess(self, text: str) -> str:
        """Layer 1: Sanitize raw LLM output before parsing.

        Handles:
        - Markdown code fences (```json, ```, etc.)
        - Text before first '{' or '[' and after last matching bracket
        - Invisible/BOM characters
        """
        text = text.strip()

        # Strip markdown code fences
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text)

        # Extract the outermost JSON object/array using bracket matching
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

        # Remove BOM and null bytes
        text = text.replace('\ufeff', '').replace('\x00', '')
        # Collapse lone \r (carriage return without following \n) which breaks JSON
        text = text.replace('\r', '\\r')

        # Remove any remaining control characters except \n and \t
        text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f]', '', text)

        return text.strip()

    # ------------------------------------------------------------------
    # Layer 2 helpers: structural fixes
    # ------------------------------------------------------------------

    def _apply_structural_fixes(self, text: str) -> str:
        """Layer 2: Fix known structural issues in LLM-generated JSON.

        Handles:
        - Unescaped newlines inside string values
        - Trailing commas before } or ]
        - Unquoted keys (gemma and mistral instruct variants do this)
        """
        # Remove trailing commas: "key": "val", }  →  "key": "val" }
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        # Fix unescaped newlines inside quoted strings
        # (the char-by-char approach preserves already-escaped content)
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

        # Fix unquoted keys: { key: "value" } → { "key": "value" }
        # Only matches word characters at the key position, not values
        # Use a negative lookbehind to avoid matching inside strings
        # Pattern: outside a string, match word characters followed by colon
        def fix_unquoted_key(m):
            key = m.group(1)
            return f'"{key}":'
        # This regex matches bare word-key followed by colon, outside strings.
        # We simulate "outside strings" by only applying it where we can find
        # unbalanced quote counts — safer: apply only to the whole block
        # and let json5 catch what regex misses.
        text = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*)\s*:(\s*[{"\[])', fix_unquoted_key, text)

        return text

    def _attempt_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse text as JSON. Returns None on failure."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    # ------------------------------------------------------------------
    # Layer 3 helpers: json5 fallback
    # ------------------------------------------------------------------

    @property
    def _json5_module(self):
        """Lazy-load json5 on first use."""
        if self._json5 is None:
            try:
                import json5 as j5
                self._json5 = j5
            except ImportError:
                self._json5 = False  # Mark as unavailable
        return self._json5

    def _try_json5(self, text: str) -> Optional[Dict[str, Any]]:
        """Layer 3: Try parsing with json5.

        json5 handles: trailing commas, unquoted keys, single-line JS comments,
        relaxed number/bool/null literals.
        """
        j5 = self._json5_module
        if not j5:
            return None
        try:
            return j5.loads(text)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Layer 4 helpers: LLM self-correction
    # ------------------------------------------------------------------

    def _self_correct(
        self,
        broken_text: str,
        system_prompt: str | None = None,
    ) -> str:
        """Layer 4: Send broken JSON back to LLM for correction.

        Args:
            broken_text: The text that failed all other layers.
            system_prompt: Original system prompt (passed through for context).

        Returns:
            Corrected JSON text (may still be invalid — caller re-runs pipeline).
        """
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

        url = f"{self.ai_config['base_url'].rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = self.ai_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = self.requests.post(
                url, json=payload, headers=headers,
                timeout=self.ai_config.get("timeout", 120)
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            # Strip fences from corrected response too
            result = re.sub(r'^```(?:json)?\s*', '', result, flags=re.MULTILINE)
            result = re.sub(r'\s*```\s*$', '', result)
            return result.strip()
        except Exception:
            # Self-correction failed — return original for caller to retry
            return broken_text

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_settings(self, settings_path: str | None = None) -> Dict[str, Any]:
        if settings_path is None:
            settings_path = "settings.json"
        path = Path(settings_path)
        if not path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")
        with open(path) as f:
            return json.load(f)