#!/usr/bin/env python3
"""Entry point for Executive Board Simulation CLI."""

import os
import sys
from pathlib import Path
from typing import Any

# Import the action item extraction utility
from src.utils import extract_action_items

# Priority 3: Memory & Learning imports
from src.memory import memory_system
from src.feedback import feedback_system
from src.knowledge_base import knowledge_base


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


def run_simulation(prompt: str, output_path: str | None = None, data_dir: str = "data",
                   summary_path: str | None = None, export_format: str | None = None) -> None:
    """Run a simulation with the given prompt."""
    # Validate settings first
    validate_settings()

    # Add this directory to path so imports work
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.agents import register_default_agents, registry
    from src.orchestrator import Orchestrator, SimulationState
    from src.utils import extract_action_items
    from src.decision_tracker import decision_tracker
    from src.summary import write_executive_summary
    from src.risk_analyzer import quantify_risks
    from src.export import (
        export_action_items_json,
        export_action_items_csv,
        export_action_items_markdown
    )

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

    # Priority 3: Inject memory context into simulation
    memory_context = memory_system.get_memory_context(prompt)
    if memory_context:
        print("\n📚 Memory context loaded from past decisions")
        state.data_corpus["memory_context.md"] = memory_context

    try:
        final_results = orchestrator.run()

        # Priority 3: Store conversation in memory
        memory_system.store_conversation(prompt, final_results)
        print("✓ Conversation stored in memory")

        # Quantify risks
        final_results = quantify_risks(final_results)

        # Write results to output file
        write_report(final_results, output_path)
        print(f"\n✓ Report written to: {output_path}")

        # Extract action items
        action_items = extract_action_items(final_results)

        # Generate executive summary if requested
        if summary_path:
            write_executive_summary(final_results, summary_path)
            print(f"✓ Executive summary written to: {summary_path}")

        # Export action items if requested
        if export_format:
            if export_format == "json":
                export_path = output_path.replace('.md', '_actions.json')
                export_action_items_json(action_items, export_path)
            elif export_format == "csv":
                export_path = output_path.replace('.md', '_actions.csv')
                export_action_items_csv(action_items, export_path)
            elif export_format == "checklist":
                export_path = output_path.replace('.md', '_checklist.md')
                export_action_items_markdown(action_items, export_path)
            else:
                print(f"Warning: Unknown export format '{export_format}'")
                export_path = None

            if export_path:
                print(f"✓ Action items exported to: {export_path}")

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

        # Agent Weight Legend (inline explanation)
        if results.get('agent_weights') and any(w > 1.0 for w in results['agent_weights'].values()):
            f.write("## Executive Weights\n\n")
            f.write("Agents with weights >1.0 have higher influence on final decision.\n\n")
            f.write("| Agent | Weight | Effect |\n")
            f.write("|-------|--------|--------|\n")
            for agent, weight in results['agent_weights'].items():
                if weight > 1.0:
                    f.write(f"| {agent.upper()} | {weight}x | Recommendations weighted {weight:.1f}x |\n")
            f.write("\n")

        # Board Decision (from CEO round-5 synthesis)
        if results.get('board_decision'):
            bd = results['board_decision']
            f.write("## Board Decision\n\n")
            if bd.get('summary'):
                f.write(f"{bd['summary']}\n\n")
            if bd.get('consensus_points'):
                f.write("### Consensus Points\n\n")
                for pt in bd['consensus_points']:
                    f.write(f"- {pt}\n")
                f.write("\n")
            if bd.get('final_priority_actions'):
                f.write("### Final Priority Actions\n\n")
                for action in bd['final_priority_actions']:
                    f.write(f"- {action}\n")
                f.write("\n")
            if bd.get('dissent_points'):
                f.write("### Dissenting Points\n\n")
                for d in bd['dissent_points']:
                    f.write(f"- {d}\n")
                f.write("\n")
            if bd.get('dissenting_opinions'):
                f.write("### Dissenting Opinions\n\n")
                for d in bd['dissenting_opinions']:
                    f.write(f"- {d}\n")
                f.write("\n")
            if bd.get('contingencies'):
                f.write("### Contingencies\n\n")
                for c in bd['contingencies']:
                    f.write(f"- {c}\n")
                f.write("\n")

        # Deliberation Transcript (rounds 1-5)
        if results.get('deliberation_rounds'):
            f.write("## Deliberation Transcript\n\n")
            for round_num in sorted(results['deliberation_rounds'].keys()):
                round_reports = results['deliberation_rounds'][round_num]
                f.write(f"### Round {round_num}\n\n")
                for agent, report in round_reports.items():
                    f.write(f"**{agent.upper()}**  ")
                    if report.get('round_number'):
                        f.write(f"(Round {report['round_number']})")
                    f.write("\n\n")
                    if report.get('summary'):
                        f.write(f"{report['summary']}\n\n")
                    if report.get('agreements'):
                        f.write("**Agreements:**\n")
                        for a in report['agreements']:
                            f.write(f"- {a}\n")
                        f.write("\n")
                    if report.get('conflicts'):
                        f.write("**Conflicts:**\n")
                        for c in report['conflicts']:
                            f.write(f"- {c}\n")
                        f.write("\n")
                    if report.get('required_changes'):
                        f.write("**Required Changes:**\n")
                        for ch in report['required_changes']:
                            f.write(f"- {ch}\n")
                        f.write("\n")
                    if report.get('revised_recommendations'):
                        f.write("**Revised Recommendations:**\n")
                        for rev in report['revised_recommendations']:
                            f.write(f"- {rev}\n")
                        f.write("\n")
                    if report.get('key_findings'):
                        f.write("**Key Findings:**\n")
                        for find in report['key_findings']:
                            f.write(f"- {find}\n")
                        f.write("\n")
                    if report.get('risks'):
                        f.write("**Risks:**\n")
                        for risk in report['risks']:
                            f.write(f"- {risk}\n")
                        f.write("\n")
                f.write("---\n\n")

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

            score = report['alignment_score']
            if score >= 0.8:
                interpretation = "High confidence (data is solid)"
            elif score >= 0.5:
                interpretation = "Moderate confidence (some uncertainty)"
            else:
                interpretation = "Low confidence (thin data, high uncertainty)"
            f.write(f"**Alignment Score:** {score:.2f} — {interpretation}\n\n")
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

        if results.get('risk_matrix'):
            f.write("## Risk Quantification\n\n")
            f.write(results['risk_matrix'])
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
        print("OpenExec - Executive Board Simulation System")
        print()
        print("Usage:")
        print("  python -m openexec run --prompt \"YOUR PROMPT\"")
        print("  python -m openexec discuss")
        print("  python -m openexec history")
        print("  python -m openexec search \"query\"")
        print("  python -m openexec feedback <decision_id>")
        print("  python -m openexec performance")
        print("  python -m openexec kb <command> [args]")
        print()
        print("Options:")
        print("  --prompt, -p       Decision prompt")
        print("  --output, -o       Output file (default: board_report.md)")
        print("  --summary          Generate executive summary")
        print("  --export           Export format (json|csv|checklist)")
        return 1

    # Parse simple arguments
    args = sys.argv[1:]

    # Check for command
    if args[0] == "discuss":
        # Start interactive discussion mode
        try:
            from src.interactive import InteractiveDiscussion
            print("Loading interactive discussion mode...")
            print("Note: This would load the last simulation results in a full implementation.")
            return 0
        except ImportError as e:
            print(f"Error: Could not load interactive mode - {e}")
            return 1

    # Priority 3: Memory commands
    if args[0] == "history":
        # Show conversation history
        history = memory_system.get_conversation_history(limit=10)
        print("\n📚 Recent Decision History\n")
        for i, conv in enumerate(history, 1):
            timestamp = conv["timestamp"]
            prompt = conv["prompt"]
            print(f"{i}. {timestamp}")
            print(f"   {prompt[:80]}...")
            print()
        return 0

    if args[0] == "search":
        # Search memory
        if len(args) < 2:
            print('Usage: python -m openexec search "query"')
            return 1
        query = args[1]
        results = memory_system.search_memory(query)
        print(f"\n🔍 Search results for: {query}\n")
        for i, conv in enumerate(results, 1):
            print(f"{i}. {conv['timestamp']}")
            print(f"   {conv['prompt'][:80]}...")
            print()
        return 0

    # Priority 3: Feedback commands
    if args[0] == "feedback":
        # Collect feedback on a decision
        if len(args) < 3:
            print("Usage: python -m openexec feedback <decision_id>")
            return 1
        decision_id = args[2]
        print(f"\n📝 Feedback for decision: {decision_id}")
        print("This would open an interactive feedback collection in a full implementation.")
        return 0

    if args[0] == "performance":
        # Show agent performance
        performance = feedback_system.get_all_agent_performance()
        print("\n📊 Agent Performance Metrics\n")
        for agent, scores in performance.items():
            print(f"{agent.upper()}:")
            print(f"  Average Rating: {scores['average_rating']:.1f}/5.0")
            print(f"  Total Ratings: {scores['total_ratings']}")
            print(f"  Success Rate: {scores['successful_outcomes']}/{scores['total_feedback']}")
            print()
        return 0

    # Priority 3: Knowledge base commands
    if args[0] == "kb":
        # Knowledge base management
        if len(args) < 2:
            print("Usage: python -m openexec kb <command> [args]")
            print("Commands: list, ingest <file>, search <query>")
            return 1

        kb_command = args[1]

        if kb_command == "list":
            docs = knowledge_base.list_documents()
            print(f"\n📚 Knowledge Base ({len(docs)} documents)\n")
            for doc in docs:
                title = doc.get('title') or doc.get('filename', 'Unknown')
                print(f"- {title} ({doc['category']})")
            return 0

        if kb_command == "ingest":
            if len(args) < 3:
                print("Usage: python -m openexec kb ingest <file> [category]")
                return 1
            file_path = args[2]
            category = args[3] if len(args) > 3 else "general"
            try:
                doc_id = knowledge_base.ingest_document(file_path, category)
                print(f"✓ Document ingested: {doc_id}")
                return 0
            except Exception as e:
                print(f"✗ Failed to ingest: {e}")
                return 1

        if kb_command == "search":
            if len(args) < 3:
                print("Usage: python -m openexec kb search <query>")
                return 1
            query = args[2]
            results = knowledge_base.retrieve_relevant(query)
            print(f"\n🔍 KB Search results for: {query}\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['doc_title']} (Score: {result['score']})")
                print(f"   {result['chunk'][:100]}...")
                print()
            return 0

        print(f"Unknown kb command: {kb_command}")
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
    summary_path = None
    export_format = None

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
        elif arg.startswith("--summary="):
            summary_path = arg.split("=", 1)[-1]
        elif arg.startswith("--export="):
            export_format = arg.split("=", 1)[-1]

    # If no prompt given, show help
    if not prompt:
        print("Usage: python -m openexec run --prompt \"YOUR PROMPT\"")
        print("       python -m openexec run --prompt \"...\" --output report.md")
        print("       python -m openexec run --prompt \"...\" --data-dir ./data")
        print("       python -m openexec run --prompt \"...\" --summary summary.md")
        print("       python -m openexec run --prompt \"...\" --export json|csv|checklist")
        print("       python -m openexec discuss")
        return 1

    run_simulation(prompt, output_path, data_dir, summary_path, export_format)
    return 0


if __name__ == "__main__":
    exit(main())
