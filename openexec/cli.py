#!/usr/bin/env python3
"""OpenExec CLI using Typer for clean, streamlined command structure."""

import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console

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

# Plain text only: no color, no automatic highlighting, no markdown/markup
# interpretation. Structure is conveyed with ASCII separators (-> => ----)
# instead of styling, and text content is shown in full, never truncated.
console = Console(markup=False, highlight=False)

SEPARATOR = "-" * 60


def print_section(title: str, body: str = "") -> None:
    """Print a plain-text section: a title framed by separator lines."""
    console.print(SEPARATOR)
    console.print(title)
    console.print(SEPARATOR)
    if body:
        console.print(body)


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
        },
        "research": {
            "enabled": False,
            "web_search_weight": 0.5,
            "knowledge_base_weight": 0.5,
            "max_context_chars": 3000
        }
    }


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    console.print(f"-> Configuration saved to {CONFIG_FILE}")


def set_nested_config(cfg: Dict[str, Any], dotted_key: str, raw_value: str) -> Any:
    """Set a (possibly dotted, e.g. 'ai.temperature') key in cfg, creating
    intermediate dicts as needed. Returns the coerced value that was stored.

    Values are parsed as JSON first (so 'true'/'false'/numbers round-trip as
    real types, matching get_default_config()'s nested bool/int/float values)
    and fall back to the raw string if that fails.
    """
    try:
        value: Any = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value

    parts = dotted_key.split(".")
    target = cfg
    for part in parts[:-1]:
        if not isinstance(target.get(part), dict):
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value
    return value


def get_nested_config(cfg: Dict[str, Any], dotted_key: str) -> Any:
    """Get a (possibly dotted) key from cfg. Raises KeyError if any segment is missing."""
    target: Any = cfg
    for part in dotted_key.split("."):
        if not isinstance(target, dict) or part not in target:
            raise KeyError(dotted_key)
        target = target[part]
    return target


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
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        help="Comma-separated list of agents to include (e.g., 'ceo,cmo'). defaults to all."
    ),
    teams: bool = typer.Option(
        False,
        "--teams",
        help="Enable hierarchical team deliberation (sub-agents report to CXOs)"
    ),
    research: bool = typer.Option(
        False,
        "--research",
        help="Ground every agent's analysis with live web search + knowledge base retrieval"
    ),
    research_mix: Optional[str] = typer.Option(
        None,
        "--research-mix",
        help="Weight ratio between web search and knowledge base (format: web=0.7,kb=0.3)"
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducible runs (requires provider support, e.g. LM Studio)"
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature",
        help="Override sampling temperature for every agent call (e.g. 0.0 for max determinism)"
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
    _run_simulation(
        prompt=prompt,
        output=output,
        summary=summary,
        export=export,
        data_dir=data_dir,
        assume=assume,
        weight=weight,
        no_memory=no_memory,
        no_feedback=no_feedback,
        agents=agents,
        teams=teams,
        research=research,
        research_mix=research_mix,
        seed=seed,
        temperature=temperature,
        verbose=verbose,
        config_override=config_override,
    )


def _run_simulation(
    prompt: Optional[str],
    output: Optional[str] = None,
    summary: Optional[str] = None,
    export: Optional[str] = None,
    data_dir: str = "data",
    assume: Optional[List[str]] = None,
    weight: Optional[List[str]] = None,
    no_memory: bool = False,
    no_feedback: bool = False,
    agents: Optional[str] = None,
    teams: bool = False,
    research: bool = False,
    research_mix: Optional[str] = None,
    seed: Optional[int] = None,
    temperature: Optional[float] = None,
    verbose: bool = False,
    config_override: Optional[Path] = None,
):
    """
    Core simulation logic behind the `run` command.

    Plain Python defaults (not typer.Option) so it can be called directly —
    e.g. from `quick`/`batch` — without going through Typer's CLI parsing.
    Calling `run()` itself directly would bind every unspecified parameter to
    its raw typer.Option/ArgumentInfo object instead of a real default.
    """
    console.print("Starting Simulation...")

    # Handle stdin
    if prompt == "-":
        console.print("Reading prompt from stdin...")
        prompt = sys.stdin.read().strip()
        if not prompt:
            console.print("ERROR: No input from stdin")
            raise typer.Exit(1)

    if not prompt:
        console.print("ERROR: Prompt is required")
        console.print("\nExamples:")
        console.print("  openexec run \"Should we buy GPUs?\"")
        console.print("  cat prompt.txt | openexec run -")
        raise typer.Exit(1)

    # Sanitize prompt to prevent prompt injection attacks
    prompt = sanitize_prompt(prompt)
    if not prompt:
        console.print("ERROR: Prompt was empty after sanitization")
        raise typer.Exit(1)

    # Load configuration
    if config_override:
        cfg = load_config() if config_override else get_default_config()
        if config_override.exists():
            with open(config_override) as f:
                cfg.update(json.load(f))
        else:
            console.print(f"WARNING: Config file {config_override} not found, using defaults")
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

    # Reproducibility overrides — applied at the provider level so they win
    # over the temperature hardcoded at each agent call site
    if seed is not None or temperature is not None:
        from openexec.ai.client import AIClient
        overrides: Dict[str, Any] = {}
        if seed is not None:
            overrides["seed"] = seed
        if temperature is not None:
            overrides["temperature_override"] = temperature
        AIClient.runtime_overrides = overrides
        parts = [f"seed={seed}" if seed is not None else "",
                 f"temperature={temperature}" if temperature is not None else ""]
        console.print(f"Reproducibility: {' '.join(p for p in parts if p)}")

    # Show banner
    print_section("OpenExec Simulation", f"Decision: {prompt}")

    # Validate settings
    settings_path = Path("settings.json")
    if not settings_path.exists():
        console.print("ERROR: settings.json not found")
        console.print("\nNext step: Run 'openexec setup' to create configuration.")
        console.print("Or manually create settings.json with your AI provider settings.")
        console.print("\nExample settings:")
        console.print(SEPARATOR)
        console.print('''{
  "ai": {
    "base_url": "http://localhost:11434/v1",
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 4096,
    "provider": "openai_compatible"
  }
}''')
        console.print(SEPARATOR)
        raise typer.Exit(1)

    # Validate output directory exists
    output_dir = Path(output).parent
    if not output_dir.exists():
        console.print(f"ERROR: Output directory does not exist: {output_dir}")
        console.print(f"Create it with: mkdir -p {output_dir}")
        raise typer.Exit(1)

    # Setup
    register_default_agents()
    state = SimulationState(
        core_prompt=prompt,
        decision_point=f"Decision required for: {prompt}",
        status="initialized"
    )

    # Set active agents if provided
    if agents:
        state.active_agents = [a.strip().lower() for a in agents.split(",")]
        console.print(f"=> Targeted simulation: {', '.join(state.active_agents)}")
    else:
        # Default to all registered agents
        state.active_agents = list(registry.list_names())

    # Parse assumptions
    if assume:
        for item in assume:
            if "=" in item:
                key, value = item.split("=", 1)
                state.assumptions[key.strip()] = value.strip()
                console.print(f"=> Assumption: {key.strip()} = {value.strip()}")
        console.print("=> Counterfactual mode enabled")

    # Parse agent weights for multi-objective optimization
    VALID_AGENTS = {"ceo", "cfo", "cto", "cmo"}
    if weight:
        for item in weight:
            if "=" in item:
                key, value = item.split("=", 1)
                agent = key.strip().lower()
                if agent not in VALID_AGENTS:
                    console.print(f"ERROR: Invalid agent name '{agent}'. Valid agents: {', '.join(sorted(VALID_AGENTS))}")
                    sys.exit(1)
                try:
                    weight_val = float(value.strip())
                    if 0.0 <= weight_val <= 1.0:
                        state.agent_weights[agent] = weight_val
                        console.print(f"=> Weight: {agent} = {weight_val}")
                    else:
                        console.print(f"ERROR: Weight must be between 0.0 and 1.0: {item}")
                        sys.exit(1)
                except ValueError:
                    console.print(f"ERROR: Invalid weight value: {item}")
                    sys.exit(1)
        console.print("=> Multi-objective optimization enabled")

    # Close the feedback loop: when the user gave no explicit weights, derive
    # them from accumulated agent ratings (needs >= 3 ratings to count)
    if not weight:
        performance = feedback_system.get_all_agent_performance()
        derived_notices = []
        for agent_name, scores in performance.items():
            agent_key = agent_name.lower()
            if agent_key in VALID_AGENTS and scores.get("total_ratings", 0) >= 3:
                avg = scores["average_rating"]
                state.agent_weights[agent_key] = round(avg / 5.0, 2)
                derived_notices.append(f"{agent_key}={state.agent_weights[agent_key]} (avg {avg:.1f}/5)")
        if derived_notices:
            console.print(f"=> Feedback-derived weights: {', '.join(derived_notices)}")

    # Configure research mix (live web search vs. knowledge base)
    research_cfg = dict(cfg.get("research", {}))
    if research:
        research_cfg["enabled"] = True
    if research_mix:
        for item in research_mix.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            key = key.strip().lower()
            try:
                weight_val = float(value.strip())
            except ValueError:
                console.print(f"ERROR: Invalid research-mix value: {item}")
                sys.exit(1)
            if key == "web":
                research_cfg["web_search_weight"] = weight_val
            elif key == "kb":
                research_cfg["knowledge_base_weight"] = weight_val
            else:
                console.print(f"ERROR: Invalid research-mix key '{key}'. Use 'web' or 'kb'.")
                sys.exit(1)
        research_cfg["enabled"] = True
    state.research_cfg = research_cfg
    if research_cfg.get("enabled"):
        console.print(
            f"=> Research grounding enabled -- web:{research_cfg.get('web_search_weight', 0.5)} "
            f"/ kb:{research_cfg.get('knowledge_base_weight', 0.5)}"
        )

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
                        console.print(f"WARNING: Could not read {file_path.name}: {e}")
    except Exception as e:
        console.print(f"WARNING: Could not access data directory: {e}")

    # Priority 3: Inject memory context
    memory_enabled = cfg.get("memory", {}).get("enabled", True) and not no_memory
    if memory_enabled and cfg.get("memory", {}).get("context_injection", True):
        memory_context = memory_system.get_memory_context(prompt)
        if memory_context:
            console.print("=> Loaded context from past decisions")
            state.data_corpus["memory_context.md"] = memory_context

    # Run simulation
    orchestrator = Orchestrator(registry, verbose=verbose)
    orchestrator.teams_enabled = teams
    orchestrator.initialize(state)

    try:
        final_results = orchestrator.run()

        # Priority 3: Store conversation
        feedback_enabled = cfg.get("feedback", {}).get("store_automatically", True) and not no_feedback
        if feedback_enabled:
            memory_system.store_conversation(prompt, final_results)
            console.print("-> Stored in memory")

        # Quantify risks (Priority 2)
        final_results = quantify_risks(final_results)

        # Write report
        write_report(final_results, output)
        console.print(f"-> Report: {output}")

        # Extract action items
        action_items = extract_action_items(final_results)

        # Generate executive summary
        if summary:
            write_executive_summary(final_results, summary)
            console.print(f"-> Summary: {summary}")

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
                console.print(f"ERROR: Unknown export format: {export}")
                raise typer.Exit(1)
            console.print(f"-> Exported: {export_path}")

        # Log decision
        decision_file = decision_tracker.log_decision(prompt, final_results, action_items)
        console.print(f"-> Logged: {Path(decision_file).name}")

        if not teams and not research:
            console.print("Tip: add --research (web+KB grounding) or --teams "
                          "(sub-agent deliberation) for deeper analysis.")

    except Exception as e:
        console.print(f"\nERROR: Simulation failed: {e}")
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
        console.print("OpenExec Setup Wizard\n")
        console.print("This will create a settings.json file in the current directory.")
        console.print("Press Enter to accept defaults or type your own values.\n")
    else:
        console.print("OpenExec Setup (non-interactive mode)\n")

    # Default settings
    defaults = {
        "ai": {
            "base_url": "http://localhost:11434/v1",
            "model": "llama3",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 120
        },
        "agents": {
            "enabled": ["ceo", "cfo", "cto", "cmo"],
        }
    }

    if default:
        settings = json.loads(json.dumps(defaults))  # Deep copy
        console.print("Using default settings.")
    else:
        settings = {}
        # Ask for AI settings
        console.print("=== AI Provider Settings ===")
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

        console.print("\n=== Agent Settings ===")
        console.print(f"Enabled Agents (default: {', '.join(defaults['agents']['enabled'])}):")
        agents = console.input()
        if agents.strip():
            settings["agents"] = defaults["agents"].copy()
            settings["agents"]["enabled"] = [a.strip().lower() for a in agents.split(",")]

    # Save settings.json
    settings_path = Path("settings.json")
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    console.print(f"\n-> Settings saved to {settings_path}")
    console.print("\nNext step: Run 'openexec run \"Your decision here\"'")


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

    Load a previous decision and ask follow-up questions against its
    stored context (prompt, agent recommendations, risks).
    """
    if decision_id:
        conv = memory_system.get_conversation(decision_id)
        if not conv:
            console.print(f"ERROR: Decision not found: {decision_id}")
            raise typer.Exit(1)
    else:
        history = memory_system.get_conversation_history(limit=1)
        if not history:
            console.print("No previous decisions found. Run 'openexec run \"...\"' first.")
            raise typer.Exit(1)
        conv = memory_system.get_conversation(history[0]["id"])

    if not Path("settings.json").exists():
        console.print("ERROR: settings.json not found -- run 'openexec setup' first.")
        raise typer.Exit(1)

    print_section(
        f"Discussing decision {conv['id']} ({conv['timestamp'][:10]})",
        f"{conv['prompt']}\n\n{conv.get('executive_summary', '')}"
    )

    context_lines = [
        "Decision context",
        f"Question: {conv['prompt']}",
        f"Executive summary: {conv.get('executive_summary', '')}",
    ]
    for agent_name, summary in conv.get("agent_summaries", {}).items():
        context_lines.append(f"\n{agent_name.upper()} -- {summary.get('title', '')}")
        for finding in summary.get("key_findings", []):
            context_lines.append(f"Finding: {finding}")
        for rec in summary.get("recommendations", []):
            context_lines.append(f"Recommendation: {rec}")
    if conv.get("overall_risk_assessment"):
        context_lines.append("\nRisks")
        for risk in conv["overall_risk_assessment"]:
            context_lines.append(f"{risk}")

    system_prompt = (
        "You are a board discussion assistant. Answer follow-up questions about the "
        "decision below using only the context provided. If the answer isn't in the "
        "context, say so. Be concise. Respond in plain text, with no markdown "
        "formatting (no **, ##, backticks, or bullet dashes).\n\n" + "\n".join(context_lines)
    )

    from openexec.ai.client import AIClient
    client = AIClient()

    console.print("\nAsk a question about this decision, or type 'exit' to quit.\n")
    while True:
        try:
            question = console.input("You: ")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        question = question.strip()
        if not question or question.lower() in {"exit", "quit"}:
            break
        try:
            answer = client.complete(question, system_prompt=system_prompt)
        except Exception as e:
            console.print(f"ERROR: {e}")
            continue
        console.print(f"Assistant: {answer}\n")


# ==============================
# Memory Commands
# ==============================

@app.command()
def history(
    limit: int = typer.Option(
        10,
        "-n", "--limit",
        help="Number of entries to show"
    )
):
    """View recent decision history."""
    conversations = memory_system.get_conversation_history(limit=limit)

    console.print(f"\nRecent Decisions ({len(conversations)})\n")

    if not conversations:
        console.print("No decisions in memory yet.")
        return

    for i, conv in enumerate(conversations, 1):
        console.print(SEPARATOR)
        console.print(f"[{i}] {conv['timestamp'][:10]}")
        console.print(conv["prompt"])
    console.print(SEPARATOR)
    console.print(f"\nTotal stored: {len(memory_system.index['conversations'])} decisions")


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
        console.print(f"\nKnowledge Base: {query} ({len(results)} results)\n")

        if not results:
            console.print("No results found.")
            return

        for result in results:
            console.print(SEPARATOR)
            console.print(f"{result['doc_title']} (score: {result['score']})")
            console.print(result['chunk'])
        console.print(SEPARATOR)
    else:
        # Search memory
        results = memory_system.search_memory(query)
        console.print(f"\nMemory: {query} ({len(results)} results)\n")

        if not results:
            console.print("No results found.")
            return

        for conv in results:
            console.print(SEPARATOR)
            console.print(conv["timestamp"][:10])
            console.print(conv["prompt"])
        console.print(SEPARATOR)


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
        console.print("No performance data yet. Provide feedback to build metrics.")
        return

    if agent:
        agent = agent.upper()
        if agent not in scores:
            console.print(f"No data for {agent}")
            return

        s = scores[agent]
        console.print(f"\n{agent} Performance\n")
        console.print(f"Average Rating: {s['average_rating']:.1f}/5.0")
        console.print(f"Total Ratings: {s['total_ratings']}")
        console.print(f"Success Rate: {s['successful_outcomes']}/{s['total_feedback']}")

        if s.get("recent_performance"):
            recent_avg = sum(r["rating"] for r in s["recent_performance"]) / len(s["recent_performance"])
            console.print(f"Recent (last {len(s['recent_performance'])}): {recent_avg:.1f}/5.0")
    else:
        console.print("\nAgent Performance\n")

        for agent_name, s in sorted(scores.items()):
            console.print(SEPARATOR)
            console.print(f"{agent_name.upper()}")
            console.print(f"Avg Rating: {s['average_rating']:.1f}/5.0")
            console.print(f"# Ratings: {s['total_ratings']}")
            console.print(f"Success Rate: {s['successful_outcomes']}/{s['total_feedback']}")
        console.print(SEPARATOR)
        console.print("\nUse 'openexec performance <AGENT>' for details")


@app.command()
def feedback(
    decision_id: str = typer.Argument(..., help="Decision ID to provide feedback for"),
    agent: Optional[str] = typer.Option(None, "-a", "--agent", help="Agent to rate"),
    rating: Optional[int] = typer.Option(None, "-r", "--rating", help="Rating 1-5"),
    outcome: Optional[str] = typer.Option(None, "-o", "--outcome", help="What happened?")
):
    """
    Provide feedback on a decision's outcome.

    Pass --agent, --rating and --outcome to record a single rating directly.
    Omit --agent to walk through every agent's recommendations interactively.
    """
    if agent:
        if rating is None or not outcome:
            console.print("ERROR: Both --rating and --outcome required when using --agent")
            raise typer.Exit(1)
        if not 1 <= rating <= 5:
            console.print("ERROR: --rating must be between 1 and 5")
            raise typer.Exit(1)
        feedback_id = feedback_system.record_feedback(
            decision_id=decision_id,
            agent=agent,
            recommendation="(not captured -- pass --agent without a stored decision context)",
            rating=rating,
            outcome=outcome
        )
        console.print(f"-> Feedback recorded: {feedback_id}")
        return

    # Interactive mode: walk through each agent's stored recommendations
    conv = memory_system.get_conversation(decision_id)
    if not conv:
        console.print(f"ERROR: Decision not found: {decision_id}")
        raise typer.Exit(1)

    agent_summaries = conv.get("agent_summaries", {})
    if not agent_summaries:
        console.print("No agent recommendations stored for this decision.")
        raise typer.Exit(1)

    console.print(f"\nFeedback for: {conv['prompt']}")
    console.print("Press Enter to skip an agent.\n")

    recorded = 0
    for agent_name, summary in agent_summaries.items():
        recs = summary.get("recommendations") or []
        console.print(SEPARATOR)
        console.print(f"{agent_name.upper()} -- {summary.get('title', '')}")
        for rec in recs:
            console.print(f"  -> {rec}")

        raw_rating = console.input("  Rating (1-5, blank to skip): ").strip()
        if not raw_rating:
            console.print()
            continue
        try:
            rating_val = int(raw_rating)
            if not 1 <= rating_val <= 5:
                raise ValueError
        except ValueError:
            console.print("  Invalid rating, skipping this agent.\n")
            continue

        outcome_val = console.input("  Outcome (what happened?): ").strip()
        if not outcome_val:
            console.print("  Outcome required, skipping this agent.\n")
            continue

        feedback_id = feedback_system.record_feedback(
            decision_id=decision_id,
            agent=agent_name,
            recommendation=" | ".join(recs) if recs else "(no recommendations recorded)",
            rating=rating_val,
            outcome=outcome_val
        )
        console.print(f"  -> Recorded ({feedback_id})\n")
        recorded += 1

    console.print(SEPARATOR)
    if recorded:
        console.print(f"-> Feedback complete: {recorded} agent(s) rated")
    else:
        console.print("No feedback recorded.")


# ==============================
# Knowledge Base Commands
# ==============================

@app.command("kb-list")
def kb_list(
    category: Optional[str] = typer.Option(None, "-c", "--category", help="Filter by category")
):
    """List knowledge base documents."""
    docs = knowledge_base.list_documents(category=category)

    console.print(f"\nKnowledge Base ({len(docs)} documents)\n")

    if not docs:
        console.print("No documents ingested yet.")
        console.print("Use: openexec kb-ingest <file> <category>")
        return

    for doc in docs:
        title = doc.get('title') or doc.get('filename', 'Unknown')
        size = f"{doc.get('size', 0):,}"
        console.print(SEPARATOR)
        console.print(f"{title}  =>  category: {doc['category']}  =>  size: {size}")
    console.print(SEPARATOR)


@app.command("kb-ingest")
def kb_ingest(
    file_path: str = typer.Argument(..., help="File to ingest"),
    category: str = typer.Option("general", "-c", "--category", help="Document category"),
    title: Optional[str] = typer.Option(None, "-t", "--title", help="Document title (defaults to filename)")
):
    """Ingest document into knowledge base."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"ERROR: File not found: {file_path}")
        raise typer.Exit(1)

    # Use title if provided
    metadata = {"title": title} if title else None

    try:
        doc_id = knowledge_base.ingest_document(file_path, category, metadata)
        console.print(f"-> Ingested into '{category}': {doc_id}")
    except Exception as e:
        console.print(f"ERROR: Failed: {e}")
        raise typer.Exit(1)


@app.command("kb-search")
def kb_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "-n", "--limit", help="Max results"),
    category: Optional[str] = typer.Option(None, "-c", "--category", help="Filter by category")
):
    """Search knowledge base for relevant content."""
    results = knowledge_base.retrieve_relevant(query, category=category, limit=limit)

    console.print(f"\nKB Search: {query} ({len(results)} results)\n")

    if not results:
        console.print("No matches found.")
        return

    for result in results:
        console.print(SEPARATOR)
        console.print(f"{result['doc_title']} (score: {result['score']})")
        console.print(result['chunk'])
    console.print(SEPARATOR)


@app.command("kb-categories")
def kb_categories():
    """List all knowledge base categories."""
    categories = knowledge_base.list_categories()

    console.print("\nKnowledge Base Categories\n")

    if not categories:
        console.print("No categories yet.")
        return

    for cat in sorted(categories):
        count = len(knowledge_base.list_documents(category=cat))
        console.print(f"  -> {cat}: {count} documents")


@app.command("kb-stats")
def kb_stats():
    """Show knowledge base statistics."""
    stats = knowledge_base.get_kb_stats()

    console.print("\nKnowledge Base Statistics\n")
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
        console.print(f"-> Created default config at {CONFIG_FILE}")
        console.print("\nEdit this file to customize defaults.")

    elif action == "set":
        if not key:
            console.print("ERROR: Key required for set action")
            raise typer.Exit(1)
        if not value:
            console.print("ERROR: Value required for set action")
            raise typer.Exit(1)

        cfg = load_config()
        coerced = set_nested_config(cfg, key, value)
        save_config(cfg)
        console.print(f"-> Set {key} = {coerced!r}")

    elif action == "get":
        if not key:
            console.print("ERROR: Key required for get action")
            raise typer.Exit(1)
        cfg = load_config()
        try:
            console.print(f"{key} = {get_nested_config(cfg, key)}")
        except KeyError:
            console.print(f"Key '{key}' not found in config")

    else:
        console.print(f"ERROR: Unknown action: {action}")
        console.print("Valid actions: show, init, set, get")
        raise typer.Exit(1)


# ==============================
# Shortcuts & Quick Actions
# ==============================

QUICK_PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {},
    "fast": {"no_memory": True, "no_feedback": True},
    "deep": {"teams": True, "research": True},
}


@app.command("quick")
def quick(
    prompt: str = typer.Argument(..., help="Quick decision prompt"),
    preset: str = typer.Option(
        "default",
        "-p", "--preset",
        help=f"Preset configuration: {', '.join(QUICK_PRESETS)}"
    )
):
    """
    Quick simulation with a named preset.

    Presets:

        default - standard run

        fast    - skip memory context injection and feedback storage, for speed

        deep    - enable --research and --teams for deeper analysis
    """
    if preset not in QUICK_PRESETS:
        console.print(
            f"ERROR: Unknown preset '{preset}'. "
            f"Valid presets: {', '.join(QUICK_PRESETS)}"
        )
        raise typer.Exit(1)

    console.print(f"=> Quick mode: {preset}")
    _run_simulation(
        prompt=prompt,
        output=f"quick_{Path(prompt).stem[:20] if len(prompt) > 20 else 'decision'}.md",
        **QUICK_PRESETS[preset]
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
            console.print(f"Decision not found: {decision_id}")
    else:
        # Show most recent
        history = memory_system.get_conversation_history(limit=1)
        if history:
            conv = history[0]
            console.print(f"Most recent: {conv['timestamp'][:10]}")
            console.print(f"ID: {conv['id']}")
            console.print(f"Prompt: {conv['prompt']}")
        else:
            console.print("No decisions in memory.")


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
        console.print("ERROR: No prompts in file")
        raise typer.Exit(1)

    console.print(f"Running {len(prompts)} simulations")

    for i, prompt in enumerate(prompts, 1):
        console.print(f"\nSimulation {i}/{len(prompts)}")
        console.print(f"Prompt: {prompt}\n")
        _run_simulation(prompt=prompt, output=f"batch_{i}_{Path(prompt).stem[:20]}.md")

    console.print(f"\n-> Batch complete: {len(prompts)} simulations")


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