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
            owner = rec[1:end_bracket]
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