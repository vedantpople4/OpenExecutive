import re
from datetime import datetime, timedelta
from typing import Any


def sanitize_prompt(prompt: str, max_length: int = 10000) -> str:
    """Sanitize user prompts to mitigate prompt injection attacks.

    Args:
        prompt: The raw user input prompt
        max_length: Maximum allowed prompt length (default: 10000 chars)

    Returns:
        Sanitized prompt string safe for injection into prompts

    Note:
        This is a defense-in-depth measure. The LLM itself should also be
        instructed to ignore attempts to override its instructions.
    """
    if not prompt:
        return ""

    # Truncate to max length
    prompt = prompt[:max_length]

    # Remove null bytes and other control characters
    prompt = prompt.replace('\x00', '')

    # Remove common injection patterns (case-insensitive)
    injection_pattern = re.compile(
        r'(\b(ignore|forget|disregard)\s+(all\s+)?(previous|prior|above)\s+(instructions?|commands?|directions?)\b)|'
        r'(\bnew\s+instructions?:)|'
        r'(\boverride\s+(your\s+)?(system|default|original)\s+(instructions?|behavior|prompt)\b)|'
        r'(<\s*script\b[^>]*>.*?<\s*/\s*script\s*>)|'
        r'(<\s*script\b[^>]*>)|'
        r'(javascript:)|'
        r'(on\w+\s*=)',
        re.IGNORECASE | re.DOTALL
    )
    prompt = injection_pattern.sub('[FILTERED]', prompt)

    # Escape potential markdown/image links that could be used for context injection
    prompt = re.sub(r'!\[.*?\]\(.*?\)', '[Image removed]', prompt)
    prompt = re.sub(r'\[.*?\]\(.*?\)', lambda m: m.group(0) if not m.group(0).startswith('[') else m.group(0), prompt)

    # Normalize whitespace
    prompt = re.sub(r'\s+', ' ', prompt).strip()

    return prompt


def _dedup_action_items(action_items):
    """Remove duplicate action items based on normalized task text."""
    seen = set()
    deduped = []
    for item in action_items:
        task_norm = item.get("task", "").strip().lower()
        if task_norm and task_norm not in seen:
            seen.add(task_norm)
            deduped.append(item)
    return deduped


def _calc_due_date(priority):
    """Calculate a due date string based on priority."""
    if priority == "HIGH":
        d = datetime.now() + timedelta(weeks=2)
        return d.strftime("%Y-%m-%d")
    elif priority == "MEDIUM":
        d = datetime.now() + timedelta(weeks=4)
        return d.strftime("%Y-%m-%d")
    return "TBD"


def extract_action_items(results: dict[str, Any]) -> list[dict[str, str]]:
    """Extract action items from the simulation results.

    Args:
        results: The simulation results dictionary

    Returns:
        List of action items with priority, task, owner, and due date
    """
    action_items = []

    # Extract from synthesized recommendations
    synthesized_recs = results.get('synthesized_recommendations', [])
    for rec in synthesized_recs:
        # Parse the recommendation to extract owner and task
        # Format: "[OWNER] Task description"
        if rec.startswith('[') and ']' in rec:
            end_bracket = rec.find(']')
            owner = rec[1:end_bracket].upper()
            task = rec[end_bracket+2:].strip()

            # Determine priority based on owner
            priority_map = {'CEO': 'HIGH', 'CFO': 'HIGH', 'CTO': 'MEDIUM', 'CMO': 'MEDIUM'}
            priority = next((prio for cxo, prio in priority_map.items() if cxo in owner.upper()), 'MEDIUM')

            action_items.append({
                'priority': priority,
                'task': task,
                'owner': owner,
                'due_date': _calc_due_date(priority)
            })

    # Also extract from individual agent recommendations if not already covered
    agent_reports = results.get('agent_reports', {})
    for agent_name, report in agent_reports.items():
        recommendations = report.get('recommendations', [])
        for rec in recommendations:
            if not isinstance(rec, str):
                continue
            # Simple heuristic: look for actionable language
            action_keywords = ['implement', 'establish', 'create', 'develop', 'build', 'allocate', 'prioritize', 'focus', 'dedicate']
            if any(keyword in rec.lower() for keyword in action_keywords):
                # Try to extract owner from the recommendation text
                owner = agent_name.upper()
                priority = 'MEDIUM'

                # Capitalize first letter and make it actionable
                if rec[0].islower():
                    task = rec[0].upper() + rec[1:]
                else:
                    task = rec

                action_items.append({
                    'priority': priority,
                    'task': task,
                    'owner': owner,
                    'due_date': _calc_due_date(priority)
                })

    return _dedup_action_items(action_items)
