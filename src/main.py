#!/usr/bin/env python3
"""Entry point for Executive Board Simulation CLI."""

import os
import sys
from pathlib import Path
from typing import Any

# Import the action item extraction utility
from src.utils import extract_action_items


def validate_settings() -> None:
    """Validate that settings.json exists and is properly configured."""
    settings_path = "settings.json"
    if not Path(settings_path).exists():
        print(f"Error: settings.json not found in current directory.")
        print("\nPlease create a settings.json file with your AI configuration.")
        print("Example settings.json:")
        print('''
{
  "ai": {
    "base_url": "http://localhost:11434/v1",
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
''')
        sys.exit(1)


def run_simulation(prompt: str, output_path: str | None = None, data_dir: str = "data") -> None:
    """Run a simulation with the given prompt."""
    # Validate settings first
    validate_settings()

    # Add this directory to path so imports work
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.agents import register_default_agents, registry
    from src.orchestrator import Orchestrator, SimulationState
    from src.utils import extract_action_items
    from src.decision_tracker import decision_tracker

    output_path = output_path or "board_report.md"

    # Register all default agents
    register_default_agents()

    # Create simulation state
    state = SimulationState(
        core_prompt=prompt,
        decision_point=f"Decision required for: {prompt}",
        status="initialized"
    )

    # Load data corpus if data directory exists
    try:
        data_path = Path(data_dir)
        if data_path.exists() and data_path.is_dir():
            for file_path in data_path.glob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        content = file_path.read_text()
                        state.data_corpus[file_path.name] = content
                    except Exception as e:
                        print(f"Warning: Could not read {file_path.name}: {e}")
    except Exception as e:
        print(f"Warning: Could not access data directory: {e}")

    # Create orchestrator and run simulation
    orchestrator = Orchestrator(registry)
    orchestrator.initialize(state)

    try:
        final_results = orchestrator.run()

        # Write results to output file
        write_report(final_results, output_path)
        print(f"\n✓ Report written to: {output_path}")

        # Extract action items
        action_items = extract_action_items(final_results)

        # Log decision
        decision_file = decision_tracker.log_decision(prompt, final_results, action_items)
        print(f"✓ Decision logged to: {decision_file}")

    except Exception as e:
        print(f"\n✗ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def write_report(results: dict[str, Any], output_path: str) -> None:
    """Write the final report to a markdown file."""
    with open(output_path, 'w') as f:
        f.write("# Executive Board Simulation Report\n\n")
        f.write(f"## Executive Summary\n\n{results['executive_summary']}\n\n")

        if results.get('decision_point'):
            f.write(f"## Decision Point\n\n{results['decision_point']}\n\n")

        f.write("## Individual Agent Reports\n\n")

        for agent_name, report in results.get('agent_reports', {}).items():
            f.write(f"### {agent_name.upper()} Report\n\n")
            f.write(f"**{report['title']}**\n\n")
            f.write(f"{report['summary']}\n\n")

            if report.get('key_findings'):
                f.write("#### Key Findings\n\n")
                for finding in report['key_findings']:
                    f.write(f"- {finding}\n")
                f.write("\n")

            if report.get('recommendations'):
                f.write("#### Recommendations\n\n")
                for rec in report['recommendations']:
                    f.write(f"- {rec}\n")
                f.write("\n")

            if report.get('risks'):
                f.write("#### Risks\n\n")
                for risk in report['risks']:
                    f.write(f"- {risk}\n")
                f.write("\n")

            f.write(f"**Confidence Score:** {report['confidence_score']:.2f}\n\n")
            f.write("---\n\n")

        if results.get('synthesized_recommendations'):
            f.write("## Synthesized Recommendations\n\n")
            for rec in results['synthesized_recommendations']:
                f.write(f"- {rec}\n")
            f.write("\n")

        # Extract action items from recommendations
        f.write("## Action Items\n\n")
        action_items = extract_action_items(results)
        if action_items:
            for item in action_items:
                priority = item.get('priority', 'MEDIUM')
                task = item.get('task', 'No task specified')
                owner = item.get('owner', 'Unassigned')
                due_date = item.get('due_date', 'TBD')
                f.write(f"- [{priority}] {task} (Owner: {owner}, Due: {due_date})\n")
        else:
            f.write("No action items identified.\n")
        f.write("\n")

        if results.get('overall_risk_assessment'):
            f.write("## Overall Risk Assessment\n\n")
            for risk in results['overall_risk_assessment']:
                f.write(f"- {risk}\n")
            f.write("\n")

        if results.get('data_sources'):
            f.write("## Data Sources\n\n")
            data_sources = results['data_sources']

            f.write(f"**Data Fetch Timestamp:** {data_sources.get('timestamp', 'Unknown')}\n\n")
            f.write(f"**Access Success Rate:** {data_sources.get('access_success_rate', 0):.1%}\n\n")

            if data_sources.get('sources_accessed'):
                f.write("### Successfully Accessed Sources\n\n")
                for source in data_sources['sources_accessed']:
                    f.write(f"- {source}\n")
                f.write("\n")

            if data_sources.get('sources_failed'):
                f.write("### Failed to Access Sources\n\n")
                for source in data_sources['sources_failed']:
                    f.write(f"- {source}\n")
                f.write("\n")

            if data_sources.get('all_available_sources'):
                f.write("### All Available Data Sources\n\n")
                for source in data_sources['all_available_sources']:
                    f.write(f"- {source}\n")
                f.write("\n")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m openexec run --prompt \"YOUR PROMPT\"")
        print("       python -m openexec discuss")  # Add discuss option
        return 1

    # Parse simple arguments
    args = sys.argv[1:]

    # Check for command
    if args[0] == "discuss":
        # Start interactive discussion mode
        try:
            from src.interactive import InteractiveDiscussion
            # For now, we'll need to load the last simulation results
            # In a real implementation, we'd load from a history file
            print("Loading interactive discussion mode...")
            print("Note: This would load the last simulation results in a full implementation.")
            return 0
        except ImportError as e:
            print(f"Error: Could not load interactive mode - {e}")
            return 1

    if args[0] != "run":
        print("Error: Only 'run' and 'discuss' commands are supported")
        print("Usage: python -m openexec run --prompt \"YOUR PROMPT\"")
        print("       python -m openexec discuss")
        return 1

    # Remove the "run" command from args
    args = args[1:]

    prompt = None
    output_path = None
    data_dir = "data"

    for arg in args:
        if arg.startswith("--prompt="):
            prompt = arg.split("=", 1)[-1]
        elif arg.startswith("-p="):
            prompt = arg.split("=", 1)[-1]
        elif arg.startswith("--output="):
            output_path = arg.split("=", 1)[-1]
        elif arg.startswith("-o="):
            output_path = arg.split("=", 1)[-1]
        elif arg.startswith("--data-dir="):
            data_dir = arg.split("=", 1)[-1]
        elif arg.startswith("-d="):
            data_dir = arg.split("=", 1)[-1]

    # If no prompt given, show help
    if not prompt:
        print("Usage: python -m openexec run --prompt \"YOUR PROMPT\"")
        print("       python -m openexec run --prompt \"...\" --output report.md")
        print("       python -m openexec run --prompt \"...\" --data-dir ./data")
        print("       python -m openexec discuss")
        return 1

    run_simulation(prompt, output_path, data_dir)
    return 0


if __name__ == "__main__":
    exit(main())
