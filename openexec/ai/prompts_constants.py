"""Shared prompt fragments for JSON correction and self-correction."""

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