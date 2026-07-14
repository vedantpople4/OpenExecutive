"""Shared JSON parsing pipeline for robust LLM response handling."""

import json
import re
from typing import Any, Dict, Optional


class JSONPipeline:
    """Four-layer JSON extraction: preprocess → fix → json → json5 → self-correct."""

    def __init__(self):
        self._json5 = None  # type: ignore

    @property
    def _json5_module(self):
        if self._json5 is None:
            try:
                import json5 as j5  # type: ignore[import-not-found]
                self._json5 = j5
            except ImportError:
                self._json5 = False
        return self._json5

    def parse(
        self,
        raw_text: str,
        system_prompt: str | None = None,
        max_correction_attempts: int = 1,
        correct_fn=None,
    ) -> Dict[str, Any]:
        """Run the 4-layer JSON extraction pipeline."""
        # Layer 1-2: preprocess + structural fixes
        text = self._preprocess(raw_text)
        fixed = self._apply_structural_fixes(text)
        parsed = self._attempt_parse(fixed)
        if parsed is not None:
            return parsed

        # Layer 3: json5
        parsed = self._try_json5(fixed)
        if parsed is not None:
            return parsed

        # Layer 4: self-correction
        if correct_fn is None:
            raise ValueError(
                f"Failed to parse LLM response as JSON.\n"
                f"Original: {raw_text[:300]}"
            )

        broken = fixed
        for _ in range(max_correction_attempts):
            corrected_text = correct_fn(broken, system_prompt=system_prompt)
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
        """Layer 1: Sanitize raw LLM output before parsing."""
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
                        text = text[start:i + 1]
                        break

        text = text.replace('﻿', '').replace('\x00', '')
        text = text.replace('\r', '\\r')
        text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f]', '', text)

        return text.strip()

    def _apply_structural_fixes(self, text: str) -> str:
        """Layer 2: Fix known structural issues in LLM-generated JSON."""
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

    def _try_json5(self, text: str) -> Optional[Dict[str, Any]]:
        j5 = self._json5_module
        if not j5:
            return None
        try:
            return j5.loads(text)
        except Exception:
            return None
