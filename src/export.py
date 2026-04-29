#!/usr/bin/env python3
"""Export action items to various formats."""

import csv
import json
from typing import Dict, Any, List


def export_action_items_json(action_items: List[Dict[str, Any]], output_path: str) -> None:
    """Export action items to JSON."""
    with open(output_path, 'w') as f:
        json.dump(action_items, f, indent=2)


def export_action_items_csv(action_items: List[Dict[str, Any]], output_path: str) -> None:
    """Export action items to CSV."""
    if not action_items:
        return

    fieldnames = ['priority', 'task', 'owner', 'due_date']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(action_items)


def export_action_items_markdown(action_items: List[Dict[str, Any]], output_path: str) -> None:
    """Export action items as markdown checklist."""
    lines = ["# Action Items", "", "- [ ] Review and prioritize tasks", ""]
    for item in action_items:
        lines.append(f"- [ ] [{item['priority']}] {item['task']} (Owner: {item['owner']}, Due: {item['due_date']})")
    lines.append("")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))