# OpenExec - Executive Board Simulation

A multi-agent simulation system that acts as an executive board, analyzing business problems from specialized C-suite perspectives.

## Quick Start

```bash
python -m openexec run \
  --prompt "Should we acquire Company X?" \
  --data-dir ./data \
  --output ./board_report.md
```

## Project Structure

```
openexec/
├── src/
│   ├── agents/          # Agent implementations (CEO, CFO, CTO, CMO)
│   ├── orchestrator.py  # Simulation orchestration logic
│   ├── config/          # Configuration files
│   └── main.py          # CLI entry point
├── data/                # Supporting documents and reports
└── tests/               # Test suite
```
