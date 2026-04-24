# Architecture Overview

## Design Principles

1. **Empty by Default** - MVP has no implementations, only scaffolding
2. **Protocol-Based** - All agents implement `AgentReport` via protocols
3. **Registry Pattern** - Agents are discoverable via `AgentRegistry`
4. **Orchestrator Separation** - Business logic separated from agent implementation
5. **Config-Driven** - Behavior controlled via YAML/environment

## Core Components

### 1. Agent Interface (`src/agents/interface.py`)
```python
class AgentReport:
    title, summary, key_findings, recommendations, risks, confidence_score
```

### 2. Agent Registry (`src/agents/__init__.py`)
- `register()` - Register agent classes
- `get()` / `list_names()` - Access registered agents

### 3. Orchestrator (`src/orchestrator.py`)
- `initialize()` - Accept briefing data
- `run_inception()` - Delegate to agents
- `run_analysis()` - Collect reports
- `run_review()` - Manage feedback loops
- `run_synthesis()` - Generate final document

### 4. CLI Entry Point (`src/main.py`)
```bash
python -m openexec run --prompt "..." --data-dir ./data
```

## Scalability Design

| Concern | MVP | Future Expansion |
|---------|------|------------------|
| **Agents** | Templates only | Full implementations with LLM calls |
| **Phases** | Stub methods | Implemented feedback loops |
| **Storage** | In-memory | Vector DB for document retrieval |
| **Configuration** | YAML | Environment + UI controls |

## Adding New Agents

1. Create `src/agents/templates_coopa.py`
2. Implement `analyze()` and `review_others()`
3. Register in `config/openexec.yaml`
4. Add to `DEFAULT_AGENTS` list
