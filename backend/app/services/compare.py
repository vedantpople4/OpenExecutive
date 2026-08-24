"""Diff logic ported from openexec/compare.py's diff_decisions, adapted to the
flat DynamoDB item shape (Section 3.6 of the plan) instead of the CLI's nested
{results: {...}} JSON-file shape — computed application-side, never a DB join."""

from __future__ import annotations

import json
from typing import Any


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def _added_and_removed(old: list[Any], new: list[Any]) -> tuple[list[Any], list[Any]]:
    def key(x: Any) -> str:
        if isinstance(x, str):
            return _norm(x)
        return _norm(json.dumps(x, default=str))

    old_keys = {key(x): x for x in old}
    new_keys = {key(x): x for x in new}
    added = [new_keys[k] for k in new_keys if k not in old_keys]
    removed = [old_keys[k] for k in old_keys if k not in new_keys]
    return added, removed


def diff_decisions(old_item: dict[str, Any], new_item: dict[str, Any]) -> dict[str, Any]:
    old_bd: dict[str, Any] = old_item.get("board_decision") or {}
    new_bd: dict[str, Any] = new_item.get("board_decision") or {}

    def list_of(d: dict[str, Any], key: str) -> list[str]:
        v = d.get(key) or []
        return [x for x in v if isinstance(x, str)]

    consensus_added, consensus_removed = _added_and_removed(
        list_of(old_bd, "consensus_points"), list_of(new_bd, "consensus_points")
    )
    dissent_added, dissent_removed = _added_and_removed(
        list_of(old_bd, "dissent_points"), list_of(new_bd, "dissent_points")
    )
    actions_added, actions_removed = _added_and_removed(
        [a.get("task", "") for a in old_item.get("action_items", [])],
        [a.get("task", "") for a in new_item.get("action_items", [])],
    )
    risks_added, risks_removed = _added_and_removed(
        list(old_item.get("overall_risk_assessment", [])),
        list(new_item.get("overall_risk_assessment", [])),
    )

    return {
        "old_prompt": old_item.get("prompt", ""),
        "new_prompt": new_item.get("prompt", ""),
        "same_prompt": _norm(old_item.get("prompt", "")) == _norm(new_item.get("prompt", "")),
        "old_summary": old_item.get("executive_summary", ""),
        "new_summary": new_item.get("executive_summary", ""),
        "consensus_added": consensus_added,
        "consensus_removed": consensus_removed,
        "dissent_added": dissent_added,
        "dissent_removed": dissent_removed,
        "actions_added": actions_added,
        "actions_removed": actions_removed,
        "risks_added": risks_added,
        "risks_removed": risks_removed,
        "agent_scores": _agent_score_deltas(old_item, new_item),
    }


def _agent_score_deltas(old_item: dict[str, Any], new_item: dict[str, Any]) -> list[dict[str, Any]]:
    old_reports: dict[str, Any] = old_item.get("agent_reports", {})
    new_reports: dict[str, Any] = new_item.get("agent_reports", {})
    agents = sorted(set(old_reports) | set(new_reports))
    deltas = []
    for agent in agents:
        old_score = old_reports.get(agent, {}).get("alignment_score")
        new_score = new_reports.get(agent, {}).get("alignment_score")
        delta = None
        if old_score is not None and new_score is not None:
            delta = round(float(new_score) - float(old_score), 2)
        deltas.append({"agent": agent, "old": old_score, "new": new_score, "delta": delta})
    return deltas
