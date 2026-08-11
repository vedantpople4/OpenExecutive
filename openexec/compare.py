"""Compare two stored decision runs.

Every run is written to ``decisions/decision_<timestamp>.json`` (full results +
action items) and indexed by ``decisions/decision_log.json``. This module loads
two of those records and diffs the parts a CEO actually cares about: the verdict,
consensus/dissent, action items, per-agent alignment, and risks.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_decision(ref: Any, log_dir: str = "decisions") -> Dict[str, Any]:
    """Resolve a reference to a stored decision record and load it.

    ``ref`` is accepted in three forms:
      - a filesystem path (existing ``decision_*.json`` file)
      - a timestamp string like ``20260731_175932`` or its ``decision_...`` name
      - an integer index into ``decision_log.json`` (1 = most recent)

    Returns the stored record dict (``{timestamp, prompt, results, action_items}``).
    """
    log_path = Path(log_dir) / "decision_log.json"

    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        log = _load_log(log_path)
        idx = int(ref) - 1
        if not 0 <= idx < len(log):
            raise FileNotFoundError(f"No decision at index {ref} in {log_path}")
        record = log[-1 - idx]  # index 1 is most recent
        return _load_record(log_path.parent / Path(record["file_path"]).name)

    path = Path(ref)
    if not path.is_absolute():
        candidates = [Path(log_dir) / path, Path(log_dir) / f"decision_{path.name}.json"]
        path = next((c for c in candidates if c.exists()), None)
    if path is None or not path.exists():
        # bare timestamp: refresh prefix match
        matches = sorted(Path(log_dir).glob(f"decision_{ref}*.json"))
        if matches:
            path = matches[0]
    if path is None or not path.exists():
        raise FileNotFoundError(f"No decision found for reference: {ref}")
    return _load_record(path)


def _load_log(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    with open(log_path) as f:
        return json.load(f)


def _load_record(path: Path) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _norm(text: str) -> str:
    """Lowercased, whitespace-collapsed text used for stable diffing."""
    return " ".join(text.split()).lower()


def _added_and_removed(old: List[str], new: List[str]) -> Tuple[List[Any], List[Any]]:
    """Return (added, removed) by normalized text between two string lists."""
    def key(x: Any) -> str:
        if isinstance(x, str):
            return _norm(x)
        return _norm(json.dumps(x, default=str))

    old_keys, new_keys = {key(x): x for x in old}, {key(x): x for x in new}
    added = [new_keys[k] for k in new_keys if k not in old_keys]
    removed = [old_keys[k] for k in old_keys if k not in new_keys]
    return added, removed


def diff_decisions(old_rec: Dict[str, Any], new_rec: Dict[str, Any]) -> Dict[str, Any]:
    """Diff two decision records into a structured comparison dict.

    ``added``/``removed`` lists are relative to *new*: ``added`` = in new but not
    old, ``removed`` = in old but not new.
    """
    old_results: Dict[str, Any] = old_rec.get("results", {})
    new_results: Dict[str, Any] = new_rec.get("results", {})

    old_bd: Dict[str, Any] = old_results.get("board_decision", {}) or {}
    new_bd: Dict[str, Any] = new_results.get("board_decision", {}) or {}

    def list_of(d: Dict[str, Any], key: str) -> List[str]:
        v = d.get(key) or []
        return [x for x in v if isinstance(x, str)]

    consensus_added, consensus_removed = _added_and_removed(
        list_of(old_bd, "consensus_points"), list_of(new_bd, "consensus_points")
    )
    dissent_added, dissent_removed = _added_and_removed(
        list_of(old_bd, "dissent_points"), list_of(new_bd, "dissent_points")
    )
    actions_added, actions_removed = _added_and_removed(
        [a.get("task", "") for a in old_rec.get("action_items", [])],
        [a.get("task", "") for a in new_rec.get("action_items", [])],
    )
    risks_added, risks_removed = _added_and_removed(
        old_results.get("overall_risk_assessment", []),
        new_results.get("overall_risk_assessment", []),
    )

    return {
        "old_prompt": old_rec.get("prompt", ""),
        "new_prompt": new_rec.get("prompt", ""),
        "same_prompt": _norm(old_rec.get("prompt", "")) == _norm(new_rec.get("prompt", "")),
        "old_summary": old_results.get("executive_summary", ""),
        "new_summary": new_results.get("executive_summary", ""),
        "consensus_added": consensus_added,
        "consensus_removed": consensus_removed,
        "dissent_added": dissent_added,
        "dissent_removed": dissent_removed,
        "actions_added": actions_added,
        "actions_removed": actions_removed,
        "risks_added": risks_added,
        "risks_removed": risks_removed,
        "agent_scores": _agent_score_deltas(old_results, new_results),
    }


def _agent_score_deltas(old_results: Dict[str, Any], new_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Per-agent alignment-score delta: old, new, and change (new - old)."""
    old_reports: Dict[str, Any] = old_results.get("agent_reports", {})
    new_reports: Dict[str, Any] = new_results.get("agent_reports", {})
    agents = sorted(set(old_reports) | set(new_reports))
    deltas = []
    for agent in agents:
        old_score = old_reports.get(agent, {}).get("alignment_score")
        new_score = new_reports.get(agent, {}).get("alignment_score")
        delta = None
        if old_score is not None and new_score is not None:
            delta = round(new_score - old_score, 2)
        deltas.append({
            "agent": agent,
            "old": old_score,
            "new": new_score,
            "delta": delta,
        })
    return deltas


def list_decisions(limit: int = 10, log_dir: str = "decisions") -> List[Dict[str, Any]]:
    """Return the ``limit`` most recent decision records (most recent first)."""
    log = _load_log(Path(log_dir) / "decision_log.json")
    recent = log[-limit:] if limit else log
    records = []
    for entry in reversed(recent):
        path = Path(log_dir) / Path(entry["file_path"]).name
        if not path.exists():
            continue
        records.append({
            "timestamp": entry.get("timestamp", ""),
            "prompt": entry.get("prompt", ""),
            "file_path": str(path),
            "record": _load_record(path),
        })
    return records


def describe_decision(rec: Dict[str, Any], index: int = 1, total: int = 1) -> str:
    """Render a stored decision record as a human-readable block.

    Shows the verdict, decision point, action items, top risks, and per-agent
    alignment scores -- the parts a CEO actually re-reads -- not just the prompt.
    """
    results: Dict[str, Any] = rec.get("results", {})
    timestamp = rec.get("timestamp", "")
    date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}" if len(timestamp) >= 8 else timestamp

    lines = []
    header = f"[{index}/{total}] {date}"
    if total > 1:
        lines.append(header)
    lines.append(f"Prompt: {rec.get('prompt', '')}")

    summary = results.get("executive_summary", "").strip()
    if summary:
        lines.append(f"Verdict: {summary}")

    decision_point = results.get("decision_point", "").strip()
    if decision_point:
        lines.append(f"Decision point: {decision_point}")

    action_items = rec.get("action_items", [])
    if action_items:
        lines.append("Action items:")
        for item in action_items[:5]:
            task = item.get("task", "")
            priority = item.get("priority", "")
            owner = item.get("owner", "")
            lines.append(f"  - [{priority}] {task} (Owner: {owner})")
        if len(action_items) > 5:
            lines.append(f"  ... and {len(action_items) - 5} more")

    risks = results.get("overall_risk_assessment", [])
    if risks:
        lines.append("Top risks:")
        for risk in risks[:3]:
            lines.append(f"  - {risk}")

    reports = results.get("agent_reports", {})
    if reports:
        parts = []
        for agent in sorted(reports):
            score = reports[agent].get("alignment_score")
            parts.append(f"{agent.upper()}:{score:.2f}" if score is not None else f"{agent.upper()}:n/a")
        lines.append("Alignment: " + " | ".join(parts))

    return "\n".join(lines)