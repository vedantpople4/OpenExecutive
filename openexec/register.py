"""Decision register: aggregate all stored decisions into an overview.

A CEO-facing dashboard pulled from ``decisions/decision_log.json`` + the per-run
records: how many decisions, how they cluster, which risks recur, and how each
executive's data alignment has trended. Pure data — the CLI renders it.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def build_register(log_dir: str = "decisions") -> Dict[str, Any]:
    """Aggregate every stored decision record into a register summary.

    Returns counts, distinct prompts, action-item totals, recurring risks,
    per-agent alignment stats, and per-month activity.
    """
    log_path = Path(log_dir) / "decision_log.json"
    if not log_path.exists():
        return _empty()

    with open(log_path) as f:
        log = json.load(f)

    if not log:
        return _empty()

    records: List[Dict[str, Any]] = []
    for entry in log:
        path = Path(log_dir) / Path(entry["file_path"]).name
        if not path.exists():
            continue
        with open(path) as f:
            records.append({"entry": entry, "record": json.load(f)})

    return {
        "total_decisions": len(records),
        "distinct_prompts": len({_norm(r["entry"].get("prompt", "")) for r in records}),
        "total_action_items": sum(len(r["record"].get("action_items", [])) for r in records),
        "high_priority_actions": sum(
            1 for r in records
            for item in r["record"].get("action_items", [])
            if item.get("priority") == "HIGH"
        ),
        "top_risks": _top_risks(records, n=5),
        "agent_alignment": _agent_alignment(records),
        "per_month": _per_month(records),
        "most_recent": records[-1]["entry"].get("timestamp", "") if records else "",
    }


def _empty() -> Dict[str, Any]:
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


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def _top_risks(records: List[Dict[str, Any]], n: int) -> List[Dict[str, str]]:
    """Most frequently recurring risks across all decisions."""
    counts: Counter = Counter()
    for r in records:
        results = r["record"].get("results", {})
        for risk in results.get("overall_risk_assessment", []):
            if isinstance(risk, str) and risk.strip():
                counts[_norm(risk)] += 1
    return [{"text": text, "count": count} for text, count in counts.most_common(n)]


def _agent_alignment(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per-agent mean alignment score and sample count across decisions."""
    per_agent: Dict[str, List[float]] = {}
    for r in records:
        reports = r["record"].get("results", {}).get("agent_reports", {})
        for agent, report in reports.items():
            score = report.get("alignment_score")
            if score is not None:
                per_agent.setdefault(agent, []).append(score)
    stats = {}
    for agent, scores in sorted(per_agent.items()):
        stats[agent] = {
            "mean": round(sum(scores) / len(scores), 2),
            "samples": len(scores),
        }
    return stats


def _per_month(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Decision counts bucketed by YYYY-MM (most recent first)."""
    counts: Counter = Counter()
    for r in records:
        ts = r["entry"].get("timestamp", "")
        if len(ts) >= 6:
            counts[ts[:6]] += 1
    return [
        {"month": month, "count": count}
        for month, count in sorted(counts.items(), reverse=True)
    ]
