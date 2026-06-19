#!/usr/bin/env python3
"""OpenExec CLI using Typer for clean, streamlined command structure."""

import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import OpenExec modules
from openexec.agents import register_default_agents, registry
from openexec.orchestrator import Orchestrator, SimulationState
from openexec.utils import extract_action_items, sanitize_prompt
from openexec.main import write_report
from openexec.decision_tracker import decision_tracker
from openexec.summary import write_executive_summary
from openexec.risk_analyzer import quantify_risks
from openexec.export import (
    export_action_items_json,
    export_action_items_csv,
    export_action_items_markdown
)
from openexec.memory import memory_system
from openexec.feedback import feedback_system
from openexec.knowledge_base import knowledge_base

app = typer.Typer(
    name="openexec",
    help="OpenExec - Executive Board Simulation System",
    add_completion=True,
    no_args_is_help=True
)

console = Console()


# ==============================
# Config Management
# ==============================

CONFIG_DIR = Path.home() / ".openexec"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "default_output": "board_report.md",
        "auto_summary": False,
        "export_format": None,
        "data_dir": "data",
        "ai": {
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "memory": {
            "enabled": True,
            "context_injection": True
        },
        "feedback": {
            "store_automatically": True
        }
    }


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    console.print(f"[green]✓ Configuration saved to {CONFIG_FILE}[/green]")


def detect_export_format(output_path: str) -> Optional[str]:
    """Auto-detect export format from output file extension."""
    ext = Path(output_path).suffix.lower()
    if ext == '.json':
        return 'json'
    elif ext == '.csv':
        return 'csv'
    elif ext in ['.md', '.markdown']:
        return 'checklist'
    return None


# ==============================
# Main Simulation Command
# ==============================

@app.command()
def run(
    prompt: Optional[str] = typer.Argument(
        None,
        help="Decision prompt (use '-' to read from stdin)"
    ),
    output: Optional[str] = typer.Option(
        None,
        "-o", "--output",
        help="Output report file (default: from config)"
    ),
    summary: Optional[str] = typer.Option(
        None,
        "-s", "--summary",
        help="Generate executive summary to this file"
    ),
    export: Optional[str] = typer.Option(
        None,
        "-e", "--export",
        help="Export action items: json, csv, checklist"
    ),
    data_dir: str = typer.Option(
        "data",
        "-d", "--data-dir",
        help="Data directory path"
    ),
    assume: Optional[List[str]] = typer.Option(
        None,
        "-a", "--assume",
        help="Counterfactual assumptions (format: key=value). Can be used multiple times."
    ),
    weight: Optional[List[str]] = typer.Option(
        None,
        "-w", "--weight",
        help="Agent weight for multi-objective optimization (format: agent=weight, e.g., cfo=0.5). Can be used multiple times."
    ),
    no_memory: bool = typer.Option(
        False,
        "--no-memory",
        help="Disable memory context injection"
    ),
    no_feedback: bool = typer.Option(
        False,
        "--no-feedback",
        help="Disable storing in feedback system"
    ),
    verbose: bool = typer.Option(
        False,
        "-v", "--verbose",
        help="Stream full agent responses, scribe synthesis, and prompt sizes to stdout"
    ),
    config_override: Optional[Path] = typer.Option(
        None,
        "-c", "--config",
        help="Use specific config file"
    )
):
    """
    Run an executive board simulation.

    Examples:

        openexec run "Should we invest in GPU infrastructure?"

        echo "Expand to Europe?" | openexec run -

        openexec run "Hire more engineers?" -o report.md -s summary.md -e csv

        openexec run "..." --data-dir ./company_data
    """

    # Handle stdin
    if prompt == "-":
        console.print("[cyan]📥 Reading prompt from stdin...[/cyan]")
        prompt = sys.stdin.read().strip()
        if not prompt:
            console.print("[red]Error:[/red] No input from stdin")
            raise typer.Exit(1)

    if not prompt:
        console.print("[red]Error:[/red] Prompt is required")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  openexec run \"Should we buy GPUs?\"")
        console.print("  cat prompt.txt | openexec run -")
        raise typer.Exit(1)

    # Sanitize prompt to prevent prompt injection attacks
    prompt = sanitize_prompt(prompt)
    if not prompt:
        console.print("[red]Error:[/red] Prompt was empty after sanitization")
        raise typer.Exit(1)

    # Load configuration
    if config_override:
        cfg = load_config() if config_override else get_default_config()
        if config_override.exists():
            with open(config_override) as f:
                cfg.update(json.load(f))
        else:
            console.print(f"[yellow]Warning: Config file {config_override} not found, using defaults[/yellow]")
    else:
        cfg = load_config()

    # Apply defaults from config
    output = output or cfg.get("default_output", "board_report.md")
    data_dir = data_dir or cfg.get("data_dir", "data")

    # Auto-detect export format if not specified but output has extension
    if not export:
        export = cfg.get("export_format") or detect_export_format(output)

    # Auto-summary if enabled in config
    if cfg.get("auto_summary") and not summary:
        summary = output.replace('.md', '_summary.md').replace('.pdf', '_summary.md')

    # Show banner
    console.print(Panel.fit(
        f"[bold]🎯 Decision[/bold]\n{prompt}",
        title="OpenExec Simulation",
        border_style="blue"
    ))

    # Validate settings
    settings_path = Path("settings.json")
    if not settings_path.exists():
        console.print("[red]Error: settings.json not found[/red]")
        console.print("\n[bold]Next step:[/bold] Run 'openexec setup' to create configuration.")
        console.print("Or manually create settings.json with your AI provider settings.")
        console.print("\n[gray]Example settings:[/gray]")
        console.print(Panel('''
{
  "ai": {
    "base_url": "http://localhost:11434/v1",
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 4096,
    "provider": "openai_compatible"
  }
}
        ''', border_style="yellow"))
        raise typer.Exit(1)

    # Validate output directory exists
    output_dir = Path(output).parent
    if not output_dir.exists():
        console.print(f"[red]Error: Output directory does not exist: {output_dir}[/red]")
        console.print(f"[gray]Create it with: mkdir -p {output_dir}[/gray]")
        raise typer.Exit(1)

    # Setup
    register_default_agents()
    state = SimulationState(
        core_prompt=prompt,
        decision_point=f"Decision required for: {prompt}",
        status="initialized"
    )

    # Parse assumptions
    if assume:
        for item in assume:
            if "=" in item:
                key, value = item.split("=", 1)
                state.assumptions[key.strip()] = value.strip()
                console.print(f"[cyan]📌 Assumption: {key.strip()} = {value.strip()}[/cyan]")
        console.print("[cyan]📌 Counterfactual mode enabled[/cyan]")

    # Parse agent weights for multi-objective optimization
    VALID_AGENTS = {"ceo", "cfo", "cto", "cmo"}
    if weight:
        for item in weight:
            if "=" in item:
                key, value = item.split("=", 1)
                agent = key.strip().lower()
                if agent not in VALID_AGENTS:
                    console.print(f"[red]Error: Invalid agent name '{agent}'. Valid agents: {', '.join(sorted(VALID_AGENTS))}[/red]")
                    sys.exit(1)
                try:
                    weight_val = float(value.strip())
                    if 0.0 <= weight_val <= 1.0:
                        state.agent_weights[agent] = weight_val
                        console.print(f"[cyan]⚖️ Weight: {agent} = {weight_val}[/cyan]")
                    else:
                        console.print(f"[red]Error: Weight must be between 0.0 and 1.0: {item}[/red]")
                        sys.exit(1)
                except ValueError:
                    console.print(f"[red]Error: Invalid weight value: {item}[/red]")
                    sys.exit(1)
        console.print("[cyan]⚖️ Multi-objective optimization enabled[/cyan]")

    # Load data corpus
    try:
        data_path = Path(data_dir)
        if data_path.exists() and data_path.is_dir():
            for file_path in data_path.glob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        content = file_path.read_text()
                        state.data_corpus[file_path.name] = content
                    except Exception as e:
                        console.print(f"[yellow]⚠ Could not read {file_path.name}: {e}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠ Could not access data directory: {e}[/yellow]")

    # Priority 3: Inject memory context
    memory_enabled = cfg.get("memory", {}).get("enabled", True) and not no_memory
    if memory_enabled and cfg.get("memory", {}).get("context_injection", True):
        memory_context = memory_system.get_memory_context(prompt)
        if memory_context:
            console.print("[cyan]📚 Loaded context from past decisions[/cyan]")
            state.data_corpus["memory_context.md"] = memory_context

    # Run simulation
    orchestrator = Orchestrator(registry, verbose=verbose)
    orchestrator.initialize(state)

    try:
        final_results = orchestrator.run()

        # Priority 3: Store conversation
        feedback_enabled = cfg.get("feedback", {}).get("store_automatically", True) and not no_feedback
        if feedback_enabled:
            memory_system.store_conversation(prompt, final_results)
            console.print("[green]✓ Stored in memory[/green]")

        # Quantify risks (Priority 2)
        final_results = quantify_risks(final_results)

        # Write report
        write_report(final_results, output)
        console.print(f"[green]✓ Report: {output}[/green]")

        # Extract action items
        action_items = extract_action_items(final_results)

        # Generate executive summary
        if summary:
            write_executive_summary(final_results, summary)
            console.print(f"[green]✓ Summary: {summary}[/green]")

        # Export action items
        if export:
            export_path = output.replace('.md', f'_actions.{export}')
            if export == "json":
                export_action_items_json(action_items, export_path)
            elif export == "csv":
                export_action_items_csv(action_items, export_path)
            elif export == "checklist":
                export_action_items_markdown(action_items, export_path)
            else:
                console.print(f"[red]✗ Unknown export format: {export}[/red]")
                raise typer.Exit(1)
            console.print(f"[green]✓ Exported: {export_path}[/green]")

        # Log decision
        decision_file = decision_tracker.log_decision(prompt, final_results, action_items)
        console.print(f"[green]✓ Logged: {Path(decision_file).name}[/green]")

    except Exception as e:
        console.print(f"\n[red]✗ Simulation failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


# ==============================
# Setup Command
# ==============================

@app.command()
def setup(
    default: bool = typer.Option(False, "--default", help="Skip prompts and use default settings (non-interactive mode)")
):
    """Create or update settings.json for AI provider configuration."""
    if not default:
        console.print("[bold]OpenExec Setup Wizard[/bold]\n")
        console.print("This will create a settings.json file in the current directory.")
        console.print("Press Enter to accept defaults or type your own values.\n")
    else:
        console.print("[bold]OpenExec Setup (non-interactive mode)[/bold]\n")

    # Default settings
    defaults = {
        "ai": {
            "base_url": "http://localhost:11434/v1",
            "model": "llama3",
            "temperature": 0.7,
            "max_tokens": 4096,
            "provider": "openai_compatible",
            "timeout": 120
        },
        "agents": {
            "enabled": ["ceo", "cfo", "cto", "cmo"],
            "analysis_depth": "medium",
            "confidence_threshold": 0.6,
            "max_interactions": 10
        },
        "output": {
            "format": "markdown",
            "include_sections": [
                "executive_summary",
                "individual_reports",
                "synthesized_recommendations",
                "risk_assessment"
            ]
        },
        "simulation": {
            "phases": [
                {"name": "inception", "weight": 0.1},
                {"name": "analysis", "weight": 0.5},
                {"name": "review", "weight": 0.25},
                {"name": "synthesis", "weight": 0.1}
            ]
        }
    }

    if default:
        settings = json.loads(json.dumps(defaults))  # Deep copy
        console.print("[green]Using default settings.[/green]")
    else:
        settings = {}
        # Ask for AI settings
        console.print("[cyan]=== AI Provider Settings ===[/cyan]")
        console.print(f"Base URL (default: {defaults['ai']['base_url']}):")
        settings["ai"] = defaults["ai"].copy()
        url = console.input()
        if url.strip():
            settings["ai"]["base_url"] = url.strip()

        console.print(f"Model (default: {defaults['ai']['model']}):")
        model = console.input()
        if model.strip():
            settings["ai"]["model"] = model.strip()

        console.print(f"Temperature (default: {defaults['ai']['temperature']}):")
        temp = console.input()
        if temp.strip():
            settings["ai"]["temperature"] = float(temp)

        console.print(f"Max Tokens (default: {defaults['ai']['max_tokens']}):")
        tokens = console.input()
        if tokens.strip():
            settings["ai"]["max_tokens"] = int(tokens)

        console.print("\n[cyan]=== Agent Settings ===[/cyan]")
        console.print(f"Enabled Agents (default: {', '.join(defaults['agents']['enabled'])}):")
        agents = console.input()
        if agents.strip():
            settings["agents"] = defaults["agents"].copy()
            settings["agents"]["enabled"] = [a.strip().lower() for a in agents.split(",")]

    # Save settings.json
    settings_path = Path("settings.json")
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    console.print(f"\n[green]✓ Settings saved to {settings_path}[/green]")
    console.print("\n[yellow]Next step:[/yellow] Run 'openexec run \"Your decision here\"'")


# ==============================
# Interactive Discussion
# ==============================

@app.command()
def discuss(
    decision_id: Optional[str] = typer.Argument(
        None,
        help="Decision ID to discuss (default: most recent)"
    )
):
    """
    Start interactive discussion mode.

    Load a previous decision and ask follow-up questions,
    challenge assumptions, or explore scenarios.
    """
    console.print("[cyan]Interactive Discussion Mode[/cyan]")
    if decision_id:
        console.print(f"Loading: {decision_id}")
    else:
        # Get most recent decision
        history = memory_system.get_conversation_history(limit=1)
        if history:
            console.print(f"Latest: {history[0]['timestamp'][:10]} - {history[0]['prompt'][:60]}...")
        else:
            console.print("[yellow]No previous decisions found.[/yellow]")
    console.print("\n[yellow]Full interactive Q&A would be implemented here.[/yellow]")
    console.print("Features: ask follow-ups, challenge agents, explore scenarios.")


# ==============================
# Memory Commands
# ==============================

@app.command()
def history(
    limit: int = typer.Option(
        10,
        "-n", "--limit",
        help="Number of entries to show"
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Show full prompts"
    )
):
    """View recent decision history."""
    conversations = memory_system.get_conversation_history(limit=limit)

    console.print(f"\n[bold]📚 Recent Decisions ({len(conversations)})[/bold]\n")

    if not conversations:
        console.print("[yellow]No decisions in memory yet.[/yellow]")
        return

    table = Table(show_header=True, expand=True)
    table.add_column("Date", style="cyan", no_wrap=True, width=10)
    table.add_column("Decision", style="white")

    for conv in conversations:
        date = conv["timestamp"][:10]
        if full:
            prompt = conv["prompt"]
        else:
            prompt = conv["prompt"][:100] + ("..." if len(conv["prompt"]) > 100 else "")
        table.add_row(date, prompt)

    console.print(table)
    console.print(f"\n[dim]Total stored: {len(memory_system.index['conversations'])} decisions[/dim]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    memory: bool = typer.Option(True, "-m", "--memory", help="Search memory"),
    kb: bool = typer.Option(False, "-k", "--kb", help="Search knowledge base"),
    limit: int = typer.Option(10, "-n", "--limit", help="Max results")
):
    """
    Search past decisions or knowledge base.

    By default searches memory. Use --kb to search knowledge base instead.
    """
    if kb:
        # Search knowledge base
        results = knowledge_base.retrieve_relevant(query, limit=limit)
        console.print(f"\n[bold]🔍 Knowledge Base: {query}[/bold] ({len(results)} results)\n")

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(show_header=True)
        table.add_column("Source", style="cyan", width=30)
        table.add_column("Score", style="green", width=6)
        table.add_column("Preview", style="white")

        for result in results:
            preview = result['chunk'][:120]
            if len(result['chunk']) > 120:
                preview += "..."
            table.add_row(result['doc_title'], str(result['score']), preview)

        console.print(table)
    else:
        # Search memory
        results = memory_system.search_memory(query)
        console.print(f"\n[bold]🔍 Memory: {query}[/bold] ({len(results)} results)\n")

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(show_header=True)
        table.add_column("Date", style="cyan", width=10)
        table.add_column("Decision", style="white")

        for conv in results:
            date = conv["timestamp"][:10]
            prompt = conv["prompt"][:100] + ("..." if len(conv["prompt"]) > 100 else "")
            table.add_row(date, prompt)

        console.print(table)


# ==============================
# Performance & Feedback
# ==============================

@app.command()
def performance(
    agent: Optional[str] = typer.Argument(
        None,
        help="Agent name (CEO, CFO, CTO, CMO)"
    )
):
    """View agent performance metrics."""
    scores = feedback_system.get_all_agent_performance()

    if not scores:
        console.print("[yellow]No performance data yet. Provide feedback to build metrics.[/yellow]")
        return

    if agent:
        agent = agent.upper()
        if agent not in scores:
            console.print(f"[yellow]No data for {agent}[/yellow]")
            return

        s = scores[agent]
        console.print(f"\n[bold]📊 {agent} Performance[/bold]\n")
        console.print(f"Average Rating: [green]{s['average_rating']:.1f}/5.0[/green]")
        console.print(f"Total Ratings: {s['total_ratings']}")
        console.print(f"Success Rate: {s['successful_outcomes']}/{s['total_feedback']}")

        if s.get("recent_performance"):
            recent_avg = sum(r["rating"] for r in s["recent_performance"]) / len(s["recent_performance"])
            console.print(f"Recent (last {len(s['recent_performance'])}): {recent_avg:.1f}/5.0")
    else:
        console.print("\n[bold]📊 Agent Performance[/bold]\n")

        table = Table(show_header=True)
        table.add_column("Agent", style="cyan")
        table.add_column("Avg Rating", style="green", justify="right")
        table.add_column("# Ratings", style="yellow", justify="right")
        table.add_column("Success Rate", style="magenta", justify="right")

        for agent_name, s in sorted(scores.items()):
            table.add_row(
                agent_name.upper(),
                f"{s['average_rating']:.1f}/5.0",
                str(s['total_ratings']),
                f"{s['successful_outcomes']}/{s['total_feedback']}"
            )

        console.print(table)
        console.print("\n[dim]Use 'openexec performance <AGENT>' for details[/dim]")


@app.command()
def feedback(
    decision_id: str = typer.Argument(..., help="Decision ID to provide feedback for"),
    agent: Optional[str] = typer.Option(None, "-a", "--agent", help="Agent to rate"),
    rating: Optional[int] = typer.Option(None, "-r", "--rating", help="Rating 1-5"),
    outcome: Optional[str] = typer.Option(None, "-o", "--outcome", help="What happened?")
):
    """Provide feedback on a decision's outcome."""
    if not agent:
        # Show interactive mode
        console.print(f"\n[bold]📝 Feedback for: {decision_id}[/bold]")
        console.print("\n[yellow]Interactive feedback mode would be implemented here.[/yellow]")
        console.print("In full version: rate individual recommendations, describe outcomes.")
        return

    if rating and outcome:
        feedback_id = feedback_system.record_feedback(
            decision_id=decision_id,
            agent=agent,
            recommendation="[summary truncated]",
            rating=rating,
            outcome=outcome
        )
        console.print(f"[green]✓ Feedback recorded: {feedback_id}[/green]")
    else:
        console.print("[red]Error:[/red] Both --rating and --outcome required when using --agent")
        raise typer.Exit(1)


# ==============================
# Knowledge Base Commands
# ==============================

@app.command("kb-list")
def kb_list(
    category: Optional[str] = typer.Option(None, "-c", "--category", help="Filter by category")
):
    """List knowledge base documents."""
    docs = knowledge_base.list_documents(category=category)

    console.print(f"\n[bold]📚 Knowledge Base ({len(docs)} documents)[/bold]\n")

    if not docs:
        console.print("[yellow]No documents ingested yet.[/yellow]")
        console.print("Use: [cyan]openexec kb-ingest <file> [category][/cyan]")
        return

    table = Table(show_header=True)
    table.add_column("Title", style="cyan")
    table.add_column("Category", style="green", width=12)
    table.add_column("Size", style="yellow", justify="right", width=10)

    for doc in docs:
        title = doc.get('title') or doc.get('filename', 'Unknown')
        size = f"{doc.get('size', 0):,}"
        table.add_row(title, doc['category'], size)

    console.print(table)


@app.command("kb-ingest")
def kb_ingest(
    file_path: str = typer.Argument(..., help="File to ingest"),
    category: str = typer.Option("general", "-c", "--category", help="Document category"),
    title: Optional[str] = typer.Option(None, "-t", "--title", help="Document title (defaults to filename)")
):
    """Ingest document into knowledge base."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]✗ File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Use title if provided
    metadata = {"title": title} if title else None

    try:
        doc_id = knowledge_base.ingest_document(file_path, category, metadata)
        console.print(f"[green]✓ Ingested into '{category}': {doc_id}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("kb-search")
def kb_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "-n", "--limit", help="Max results"),
    category: Optional[str] = typer.Option(None, "-c", "--category", help="Filter by category")
):
    """Search knowledge base for relevant content."""
    results = knowledge_base.retrieve_relevant(query, category=category, limit=limit)

    console.print(f"\n[bold]🔍 KB Search: {query}[/bold] ({len(results)} results)\n")

    if not results:
        console.print("[yellow]No matches found.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Source", style="cyan", width=30)
    table.add_column("Score", style="green", width=6)
    table.add_column("Preview", style="white")

    for result in results:
        preview = result['chunk'][:150]
        if len(result['chunk']) > 150:
            preview += "..."
        table.add_row(result['doc_title'], str(result['score']), preview)

    console.print(table)


@app.command("kb-categories")
def kb_categories():
    """List all knowledge base categories."""
    categories = knowledge_base.list_categories()

    console.print("\n[bold]📂 Knowledge Base Categories[/bold]\n")

    if not categories:
        console.print("[yellow]No categories yet.[/yellow]")
        return

    for cat in sorted(categories):
        count = len(knowledge_base.list_documents(category=cat))
        console.print(f"  [cyan]{cat}[/cyan]: {count} documents")


@app.command("kb-stats")
def kb_stats():
    """Show knowledge base statistics."""
    stats = knowledge_base.get_kb_stats()

    console.print("\n[bold]📊 Knowledge Base Statistics[/bold]\n")
    console.print(f"Documents: {stats['total_documents']}")
    console.print(f"Chunks: {stats['total_chunks']}")
    console.print(f"Categories: {', '.join(stats['categories'])}")
    console.print(f"Last Updated: {stats['last_updated'][:19] if stats['last_updated'] else 'Never'}")


# ==============================
# Aliases for common commands
# ==============================

@app.command()
def list_docs():
    """Alias for kb-list."""
    kb_list()


@app.command()
def ingest(
    file_path: str = typer.Argument(..., help="File to ingest"),
    category: str = typer.Option("general", "-c", "--category", help="Document category")
):
    """Alias for kb-ingest."""
    kb_ingest(file_path, category)


# ==============================
# Config Management
# ==============================

@app.command("config")
def config_command(
    action: str = typer.Argument("show", help="Action: show, init, set, get"),
    key: Optional[str] = typer.Argument(None, help="Configuration key"),
    value: Optional[str] = typer.Argument(None, help="Configuration value")
):
    """
    Manage configuration.

    Actions:

        show   - Show current configuration

        init   - Create default config file

        set    <key> <value> - Set a configuration value

        get    <key>         - Get a configuration value
    """

    if action == "show":
        cfg = load_config()
        console.print(json.dumps(cfg, indent=2))

    elif action == "init":
        if CONFIG_FILE.exists():
            if not typer.confirm(f"Config exists at {CONFIG_FILE}. Overwrite?"):
                return
        cfg = get_default_config()
        save_config(cfg)
        console.print(f"[green]✓ Created default config at {CONFIG_FILE}[/green]")
        console.print("\nEdit this file to customize defaults.")

    elif action == "set":
        if not key:
            console.print("[red]Error:[/red] Key required for set action")
            raise typer.Exit(1)
        if not value:
            console.print("[red]Error:[/red] Value required for set action")
            raise typer.Exit(1)

        cfg = load_config()
        # Support nested keys like "ai.temperature"?? For now simple
        cfg[key] = value
        save_config(cfg)
        console.print(f"[green]✓ Set {key} = {value}[/green]")

    elif action == "get":
        if not key:
            console.print("[red]Error:[/red] Key required for get action")
            raise typer.Exit(1)
        cfg = load_config()
        if key in cfg:
            console.print(f"{key} = {cfg[key]}")
        else:
            console.print(f"[yellow]Key '{key}' not found in config[/yellow]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: show, init, set, get")
        raise typer.Exit(1)


# ==============================
# Shortcuts & Quick Actions
# ==============================

@app.command("quick")
def quick(
    prompt: str = typer.Argument(..., help="Quick decision prompt"),
    preset: str = typer.Option("default", "-p", "--preset", help="Preset configuration")
):
    """
    Quick simulation with preset configuration.

    Uses optimized defaults for fast execution.
    """
    console.print(f"[cyan]⚡ Quick mode: {preset}[/cyan]")
    # In full version, would load preset config
    # For now, just run with minimal output
    run(
        prompt=prompt,
        output=f"quick_{Path(prompt).stem[:20] if len(prompt) > 20 else 'decision'}.md"
    )


@app.command()
def review(
    decision_id: Optional[str] = typer.Argument(None, help="Decision ID to review")
):
    """Review a previous decision (open in default viewer)."""
    if decision_id:
        conv = memory_system.get_conversation(decision_id)
        if conv:
            console.print(f"Decision: {conv['timestamp'][:10]}")
            console.print(f"Prompt: {conv['prompt']}")
        else:
            console.print(f"[red]Decision not found: {decision_id}[/red]")
    else:
        # Show most recent
        history = memory_system.get_conversation_history(limit=1)
        if history:
            conv = history[0]
            console.print(f"Most recent: {conv['timestamp'][:10]}")
            console.print(f"ID: {conv['id']}")
            console.print(f"Prompt: {conv['prompt']}")
        else:
            console.print("[yellow]No decisions in memory.[/yellow]")


# ==============================
# Batch Operations (Basic)
# ==============================

@app.command()
def batch(
    file: typer.FileText = typer.Argument(..., help="File with prompts (one per line)")
):
    """Run multiple simulations from a file."""
    prompts = [line.strip() for line in file if line.strip()]

    if not prompts:
        console.print("[red]Error:[/red] No prompts in file")
        raise typer.Exit(1)

    console.print(f"[cyan]Running {len(prompts)} simulations[/cyan]")

    for i, prompt in enumerate(prompts, 1):
        console.print(f"\n[bold]Simulation {i}/{len(prompts)}[/bold]")
        console.print(f"Prompt: {prompt}\n")
        run(prompt=prompt, output=f"batch_{i}_{Path(prompt).stem[:20]}.md")

    console.print(f"\n[green]✓ Batch complete: {len(prompts)} simulations[/green]")


# ==============================
# Main Entry Point
# ==============================

def main():
    """Main entry point."""
    # Ensure config directory exists
    ensure_config_dir()
    app()

if __name__ == "__main__":
    main()