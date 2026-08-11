"""Render a simulation's results as a self-contained, board-ready HTML page.

Mirrors the markdown report (openexec/main.py) section for section, but as a
standalone HTML file with inline CSS -- no external assets, safe to open from
disk or email to stakeholders. Escapes all model text so it renders, never
executes.
"""

import html
from typing import Any, Dict, List

from openexec.utils import extract_action_items


def _esc(text: Any) -> str:
    """Escape arbitrary model text for safe HTML rendering."""
    return html.escape(str(text), quote=False)


def _list_html(items: List[Any], tag: str = "li") -> str:
    if not items:
        return ""
    rows = "\n".join(f"<{tag}>{_esc(x)}</{tag}>" for x in items)
    return f"<ul>\n{rows}\n</ul>"


def _board_decision_html(bd: Dict[str, Any]) -> str:
    if not bd:
        return ""
    parts = []
    if bd.get("summary"):
        parts.append(f"<p>{_esc(bd['summary'])}</p>")
    if bd.get("consensus_points"):
        parts.append(f"<h3>Consensus</h3>{_list_html(bd['consensus_points'])}")
    if bd.get("dissent_points"):
        parts.append(f"<h3>Dissent</h3>{_list_html(bd['dissent_points'])}")
    if bd.get("final_priority_actions"):
        parts.append(f"<h3>Priority Actions</h3>{_list_html(bd['final_priority_actions'])}")
    if bd.get("contingencies"):
        parts.append(f"<h3>Contingencies</h3>{_list_html(bd['contingencies'])}")
    if bd.get("dissenting_opinions"):
        parts.append(f"<h3>Dissenting Opinions</h3>{_list_html(bd['dissenting_opinions'])}")
    return "\n".join(parts)


def render_html_report(results: Dict[str, Any]) -> str:
    """Return a full standalone HTML page for the given simulation results."""
    board_decision = _board_decision_html(results.get("board_decision", {}) or {})

    agent_sections = []
    for agent_name, report in (results.get("agent_reports", {}) or {}).items():
        badge = ""
        if report.get("is_fallback"):
            badge = ' <span class="badge badge-fallback">FALLBACK STUB — AI call failed</span>'
        parts = [f"<h2>{_esc(agent_name.upper())} Report{badge}</h2>"]
        if report.get("title"):
            parts.append(f"<p class=\"subtitle\">{_esc(report['title'])}</p>")
        if report.get("summary"):
            parts.append(f"<p>{_esc(report['summary'])}</p>")
        if report.get("key_findings"):
            parts.append(f"<h3>Key Findings</h3>{_list_html(report['key_findings'])}")
        if report.get("recommendations"):
            parts.append(f"<h3>Recommendations</h3>{_list_html(report['recommendations'])}")
        if report.get("risks"):
            parts.append(f"<h3>Risks</h3>{_list_html(report['risks'])}")
        grounding = report.get("grounding")
        if grounding and grounding.get("claims_checked"):
            line = (f"{grounding['claims_grounded']}/{grounding['claims_checked']} "
                    "numeric claims found in source data")
            if grounding.get("ungrounded"):
                line += f" — unverified: {_esc(', '.join(grounding['ungrounded'][:5]))}"
            parts.append(f"<p class=\"meta\">Grounding: {line}</p>")
        score = report.get("alignment_score")
        if score is not None:
            parts.append(f"<p class=\"meta\">Alignment Score: {score:.2f}</p>")
        agent_sections.append('<section class="card">' + "\n".join(parts) + "</section>")

    action_items = extract_action_items(results)
    actions_html = _list_html(
        [f"[{item.get('priority', 'MEDIUM')}] {item.get('task', '')} "
         f"(Owner: {item.get('owner', 'Unassigned')}, Due: {item.get('due_date', 'TBD')})"
         for item in action_items]
    ) if action_items else "<p>No action items identified.</p>"

    risk_matrix = results.get("risk_matrix", "")
    risks_html = (f"<pre>{_esc(risk_matrix)}</pre>" if risk_matrix
                  else _list_html(results.get("overall_risk_assessment", [])))

    sections = []
    if results.get("executive_summary"):
        sections.append(f"<section><h2>Executive Summary</h2>"
                        f"<p>{_esc(results['executive_summary'])}</p></section>")
    if board_decision:
        sections.append(f"<section><h2>Board Decision</h2>{board_decision}</section>")
    if results.get("synthesized_recommendations"):
        sections.append(f"<section><h2>Synthesized Recommendations</h2>"
                        f"{_list_html(results['synthesized_recommendations'])}</section>")
    sections.append(f"<section><h2>Action Items</h2>{actions_html}</section>")
    if risks_html:
        sections.append(f"<section><h2>Risk Quantification</h2>{risks_html}</section>")
    sections.append("<section><h2>Agent Reports</h2>" + "\n".join(agent_sections) + "</section>")

    return _page("\n".join(sections))


def _page(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenExec Board Report</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
         max-width: 860px; margin: 2rem auto; padding: 0 1rem;
         color: #1a1a1a; line-height: 1.55; background: #fafafa; }}
  h1 {{ border-bottom: 3px solid #1a1a1a; padding-bottom: .4rem; }}
  h2 {{ margin-top: 1.8rem; border-bottom: 1px solid #ddd; padding-bottom: .2rem; }}
  h3 {{ margin-bottom: .3rem; }}
  .card {{ background: #fff; border: 1px solid #e3e3e3; border-radius: 8px;
          padding: 1rem 1.25rem; margin: .75rem 0; }}
  .subtitle {{ color: #555; font-style: italic; margin-top: -0.4rem; }}
  .meta {{ color: #555; font-size: .92em; }}
  .badge {{ font-size: .75em; font-weight: 600; padding: .15em .5em;
           border-radius: 999px; vertical-align: middle; }}
  .badge-fallback {{ background: #ffe9e9; color: #a33; }}
  pre {{ background: #f1f1f1; padding: .75rem; border-radius: 6px; overflow-x: auto; }}
  ul {{ margin-top: .25rem; }}
  li {{ margin: .2rem 0; }}
  footer {{ margin-top: 2.5rem; color: #888; font-size: .85em;
           border-top: 1px solid #ddd; padding-top: .6rem; }}
</style>
</head>
<body>
<h1>Executive Board Simulation Report</h1>
{body}
<footer>Generated by OpenExec — AI-generated analysis. Verify high-stakes claims before acting.</footer>
</body>
</html>
"""


def write_html_report(results: Dict[str, Any], output_path: str) -> None:
    """Render ``results`` to a standalone HTML page and write it to disk."""
    with open(output_path, 'w') as f:
        f.write(render_html_report(results))
