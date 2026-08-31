# Asset inventory — OpenExec improvements promo

No website was captured (OpenExec is a CLI tool — nothing to crawl). Assets are
real outputs generated from the actual tool in this session.

| Asset | Source | Use |
|---|---|---|
| `demo_board_report.md` | `openexec demo` renderer (write_report) | The core artifact — a full board report from the canned demo. Revealed frame by frame. |
| `demo_board_report.html` | `openexec demo` renderer (write_html_report) | The standalone board-ready HTML export. Final beat. |
| `help.txt` | `openexec --help` | Command list — 22 commands including the 6 new ones. |
| `dry_run.txt` | `openexec run ... --dry-run` | Cost/ETA pre-run estimate — "9-15 calls, 3m-5m". |
| `history.txt` | `openexec history -n 3` | Real decision history with verdicts. |
| `register.txt` | `openexec register` | The dashboard — totals, recurring risks, alignment. |
| `compare.txt` | `openexec compare 2 1` | Run-to-run diff output. |

Key numbers to feature (real, from this repo):
- 440 tests (was 18 at the LinkedIn-version) — 22×
- 6 new commands
- 22 commands total
- 97% coverage on the value surface (main/risk/grounding/export/event_store)
- CI: Python 3.10 / 3.12 / 3.14, ruff + pytest + coverage gate + secrets scan
- demo mode: zero LLM required

No brand colors or fonts captured (CLI tool) — the frame preset supplies the
design system.
