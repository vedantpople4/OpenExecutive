"""Blends live web search and the local knowledge base into a single research context.

The mix between the two sources is controlled by weights in research_cfg so
users can dial up/down external grounding vs. proprietary company data.
"""

from typing import Any, Dict, List, Tuple

from openexec.data.websearch import web_search
from openexec.knowledge_base import knowledge_base


def build_research_context(
    query: str,
    research_cfg: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """Fetch and blend web search + knowledge base results for a query.

    Args:
        query: The core decision prompt to research.
        research_cfg: {"enabled": bool, "web_search_weight": float,
                       "knowledge_base_weight": float, "max_context_chars": int}

    Returns:
        (formatted_markdown_block, metadata). Block is "" if research is
        disabled or both sources came back empty. Metadata tracks which
        sources were used, for the data_sources audit trail.
    """
    cfg = research_cfg or {}
    if not cfg.get("enabled"):
        return "", {}

    web_weight = max(0.0, cfg.get("web_search_weight", 0.5))
    kb_weight = max(0.0, cfg.get("knowledge_base_weight", 0.5))
    total_weight = web_weight + kb_weight
    if total_weight == 0:
        return "", {}

    max_chars = cfg.get("max_context_chars", 3000)
    web_budget = int(max_chars * web_weight / total_weight)
    kb_budget = int(max_chars * kb_weight / total_weight)

    sections: List[str] = []
    sources_used: List[str] = []

    if web_budget > 0:
        web_results = web_search(query, max_results=3)
        if web_results:
            lines = []
            for r in web_results:
                lines.append(f"- **{r['title']}** ({r['url']}): {r['content']}")
                sources_used.append(r["url"])
            sections.append("### Live Web Search\n" + "\n".join(lines)[:web_budget])

    if kb_budget > 0:
        kb_results = knowledge_base.retrieve_relevant(query, limit=3)
        if kb_results:
            lines = []
            for r in kb_results:
                lines.append(f"- **{r['doc_title']}**: {r['chunk']}")
                sources_used.append(r["doc_title"])
            sections.append("### Knowledge Base\n" + "\n".join(lines)[:kb_budget])

    if not sections:
        return "", {}

    block = (
        "## Research Context\n"
        "Use the following for grounding. Synthesize the insight, do not quote verbatim.\n\n"
        + "\n\n".join(sections)
    )
    return block, {"research_sources": sources_used}
