"""Aggregate logic ported from openexec/register.py's build_register, adapted
to a Scan over openexec-decisions instead of decisions/decision_log.json.
Computed on demand (Section 3.7 of the plan) — no maintained counters."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def _empty() -> dict[str, Any]:
    return {
        "total_decisions": 0,
        "distinct_prompts": 0,
        "total_action_items": 0,
        "high_priority_actions": 0,
        "top_risks": [],
        "agent_alignment": {},
        "per_month": [],
        "most_recent": "",
    }


def _top_risks(items: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    counts: Counter = Counter()
    for item in items:
        for risk in item.get("overall_risk_assessment", []):
            if isinstance(risk, str) and risk.strip():
                counts[_norm(risk)] += 1
    return [{"text": text, "count": count} for text, count in counts.most_common(n)]


def _agent_alignment(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    per_agent: dict[str, list[float]] = {}
    for item in items:
        for agent, report in item.get("agent_reports", {}).items():
            score = report.get("alignment_score")
            if score is not None:
                per_agent.setdefault(agent, []).append(float(score))

    stats: dict[str, dict[str, Any]] = {}
    for agent, scores in sorted(per_agent.items()):
        stats[agent] = {"mean": round(sum(scores) / len(scores), 2), "samples": len(scores)}
    return stats


def _per_month(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter = Counter()
    for item in items:
        created_at = item.get("created_at", "")
        if len(created_at) >= 7:
            counts[created_at[:7]] += 1  # "YYYY-MM"
    return [
        {"month": month, "count": count} for month, count in sorted(counts.items(), reverse=True)
    ]


def build_register(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return _empty()

    return {
        "total_decisions": len(items),
        "distinct_prompts": len({_norm(item.get("prompt", "")) for item in items}),
        "total_action_items": sum(len(item.get("action_items", [])) for item in items),
        "high_priority_actions": sum(
            1
            for item in items
            for action in item.get("action_items", [])
            if action.get("priority") == "HIGH"
        ),
        "top_risks": _top_risks(items, n=5),
        "agent_alignment": _agent_alignment(items),
        "per_month": _per_month(items),
        "most_recent": max(item.get("created_at", "") for item in items),
    }
