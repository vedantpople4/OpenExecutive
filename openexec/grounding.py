"""Deterministic grounding check — do agents' numeric claims appear in the source data?

No LLM calls. Extracts numeric claims (currency, percentages, multipliers,
latencies, time spans) from report text and checks each one literally against
the data corpus. An unmatched claim is "unverified", not false — agents may
legitimately derive numbers that don't appear verbatim in any source.
"""

import re
from typing import Any, Dict

# Numeric claims worth verifying. Bare numbers are skipped — too noisy
# ("round 2", "3 conflicts") — only numbers with a unit or symbol attached.
_CLAIM_RE = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d+)?\s?(?:[MKBmkb](?:illion)?\b)?"
    r"|\b\d[\d,]*(?:\.\d+)?\s?(?:%|ms\b|GB\b|TB\b|x\b)"
    r"|\b\d[\d,]*(?:\.\d+)?\s?(?:eng-weeks?|weeks?|months?|days?|hours?|years?)\b",
    re.IGNORECASE,
)

_REPORT_TEXT_FIELDS = ("key_findings", "risks")


def _normalize(text: str) -> str:
    """Lowercase and strip whitespace/commas so '$2 M' matches '$2m'."""
    return re.sub(r"[\s,]", "", text.lower())


def extract_numeric_claims(text: str) -> list[str]:
    """Return numeric claims found in text, in order of appearance."""
    return [m.group(0).strip() for m in _CLAIM_RE.finditer(text)]


def check_report_grounding(
    report: Dict[str, Any],
    data_corpus: Dict[str, str],
) -> Dict[str, Any]:
    """Check a report dict's numeric claims against the data corpus.

    Returns {claims_checked, claims_grounded, ungrounded} or {} when there is
    nothing to check (no corpus, or no numeric claims in the report).
    """
    if not data_corpus:
        return {}

    texts = []
    if report.get("summary"):
        texts.append(str(report["summary"]))
    for field in _REPORT_TEXT_FIELDS:
        for item in report.get(field) or []:
            texts.append(str(item))

    claims: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for claim in extract_numeric_claims(text):
            key = _normalize(claim)
            if key not in seen:
                seen.add(key)
                claims.append(claim)

    if not claims:
        return {}

    corpus_norm = _normalize(" ".join(data_corpus.values()))
    ungrounded = [c for c in claims if _normalize(c) not in corpus_norm]

    return {
        "claims_checked": len(claims),
        "claims_grounded": len(claims) - len(ungrounded),
        "ungrounded": ungrounded,
    }
