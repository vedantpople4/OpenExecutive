#!/usr/bin/env python3
"""Entry point for Executive Board Simulation CLI."""

import sys
from pathlib import Path
from typing import Any


def run_simulation(prompt: str, output_path: str | None = None, data_dir: str = "data") -> None:
    """Run a simulation with the given prompt."""
    # Add this directory to path so imports work
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.agents import register_default_agents, registry
    from src.orchestrator import Orchestrator, SimulationState

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

        if results.get('overall_risk_assessment'):
            f.write("## Overall Risk Assessment\n\n")
            for risk in results['overall_risk_assessment']:
                f.write(f"- {risk}\n")
            f.write("\n")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m openexec run --prompt \"YOUR PROMPT\"")
        return 1

    # Parse simple arguments
    args = sys.argv[1:]

    # Check for command
    if args[0] != "run":
        print("Error: Only 'run' command is supported")
        print("Usage: python -m openexec run --prompt \"YOUR PROMPT\"")
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
        return 1

    run_simulation(prompt, output_path, data_dir)
    return 0


if __name__ == "__main__":
    exit(main())
