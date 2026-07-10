"""Free web search via the ddgs package (no API key required)."""

from typing import Any, Dict, List


def web_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Run a DuckDuckGo search and return structured results.

    Returns a list of {title, url, content} dicts. Returns an empty list
    if the ddgs package is unavailable or the search fails (no network,
    rate limited, etc.) -- callers should treat this as a soft failure,
    same as a failed data_corpus file read.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return []

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "content": r.get("body", ""),
        }
        for r in raw_results
    ]
