from openexec.ai.abstract_provider import BaseProvider
import requests
import json
import re
from typing import Any, Dict, Optional


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


class OllamaProvider(BaseProvider):
    """Provider for Ollama-compatible LLMs (e.g., Ollama with local models like llama3, gemma, etc.).

    This provider uses the Ollama API at the local machine (default: http://localhost:11434)."""

    def __init__(self, ai_config: Dict[str, Any]):
        super().__init__(ai_config)
        self.ai_config = ai_config
        self.base_url = ai_config.get("base_url", "http://localhost:11434")
        self.base_url = self.base_url.rstrip('/')
        self._json5 = None

    def complete(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Complete a prompt using the OpenAI-compatible API (LM Studio, Ollama with API compat, etc.)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.ai_config.get("model", "llama3"),
            "messages": messages,
            "max_tokens": max_tokens if max_tokens is not None else self.ai_config.get("max_tokens", 4096),
            "temperature": temperature if temperature is not None else self.ai_config.get("temperature", 0.7),
        }
        
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
        return self._parse_with_pipeline(raw_response, system_prompt=system_prompt)

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
        return self._parse_with_pipeline(
            raw_response, 
            system_prompt=system_prompt, 
            max_correction_attempts=max_attempts - 1
        )

    # ------------------------------------------------------------------
    # Layer pipeline (Shared with AIClient, but only needed for Ollama)
    # ------------------------------------------------------------------

    def _parse_with_pipeline(self, raw_text: str, system_prompt: Optional[str] = None, max_correction_attempts: int = 1) -> Dict[str, Any]:
        """Run the 4-layer JSON extraction pipeline."""
        # Layer 1: preprocess
        text = self._preprocess(raw_text)

        # Layer 2: attempt standard parse with fixes
        fixed = self._apply_structural_fixes(text)
        parsed = self._attempt_parse(fixed)
        if parsed is not None:
            return parsed

        # Layer 3: try json5 (handles trailing commas, unquoted keys, single-line JS comments)
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

        raise ValueError(
            f"Failed to parse LLM response as JSON after 4 layers.\n"
            f"Original (first 300 chars): {raw_text[:300]}\n"
            f"Last attempted (first 300 chars): {broken[:300]}"
        )

    # --- Private Helpers for Layers ---

    def _preprocess(self, text: str) -> str:
        """Layer 1: Sanitize raw LLM output before parsing."""
        text = text.strip()

        # Strip markdown code fences from anywhere in text
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)

        # Extract the outermost JSON object/array using string-aware bracket matching
        start = -1
        for i, ch in enumerate(text):
            if ch in ('{', '['):
                start = i
                break

        if start >= 0:
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start, len(text)):
                ch = text[i]
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\':
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if not in_string:
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

    def _apply_structural_fixes(self, text: str) -> str:
        """Layer 2: Fix known structural issues in LLM-generated JSON."""
        # Remove trailing commas: "key": "val", }  →  "key": "val" }
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        # Fix unescaped newlines inside quoted strings
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
        def fix_unquoted_key(m):
            key = m.group(1)
            return f'"{key}":'
        text = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*)\s*:(\s*[{"\[])', fix_unquoted_key, text)

        return text

    def _attempt_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse text as JSON. Returns None on failure."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

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
        """Layer 3: Try parsing with json5."""
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
        system_prompt: Optional[str] = None,
    ) -> str:
        """Layer 4: Send broken JSON back to LLM for correction."""
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