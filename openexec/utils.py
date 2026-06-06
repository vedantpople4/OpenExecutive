import re
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
    injection_patterns = [
        r'\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|commands?|directions?)\b',
        r'\bforget\s+(all\s+)?(previous|prior|above)\s+(instructions?|commands?)\b',
        r'\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|commands?)\b',
        r'\bnew\s+instructions?:',
        r'\boverride\s+(your\s+)?(system|default|original)\s+(instructions?|behavior|prompt)\b',
        r'<\s*script\b[^>]*>.*?<\s*/\s*script\s*>',  # Full <script>...</script> tags
        r'<\s*script\b[^>]*>',  # Opening <script> tag
        r'javascript:',
        r'on\w+\s*=',  # Event handlers like onclick=, onerror=
    ]

    for pattern in injection_patterns:
        if 'script' in pattern.lower():
            prompt = re.sub(pattern, '[FILTERED]', prompt, flags=re.IGNORECASE | re.DOTALL)
        else:
            prompt = re.sub(pattern, '[FILTERED]', prompt, flags=re.IGNORECASE)

    # Escape potential markdown/image links that could be used for context injection
    prompt = re.sub(r'!\[.*?\]\(.*?\)', '[Image removed]', prompt)
    prompt = re.sub(r'\[.*?\]\(.*?\)', lambda m: m.group(0) if not m.group(0).startswith('[') else m.group(0), prompt)

    # Normalize whitespace
    prompt = re.sub(r'\s+', ' ', prompt).strip()

    return prompt


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
            priority_map = {
                'CEO': 'HIGH',
                'CFO': 'HIGH',
                'CTO': 'MEDIUM',
                'CMO': 'MEDIUM'
            }

            priority = 'MEDIUM'  # default
            for cxo, prio in priority_map.items():
                if cxo in owner.upper():
                    priority = prio
                    break

            action_items.append({
                'priority': priority,
                'task': task,
                'owner': owner,
                'due_date': 'TBD'
            })

    # Also extract from individual agent recommendations if not already covered
    agent_reports = results.get('agent_reports', {})
    for agent_name, report in agent_reports.items():
        recommendations = report.get('recommendations', [])
        for rec in recommendations:
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
                    'due_date': 'TBD'
                })

    return action_items