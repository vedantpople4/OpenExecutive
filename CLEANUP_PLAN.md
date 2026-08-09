# OpenExec Cleanup Plan

> Based on `ponytail:ponytail-audit` — 22 findings, ~500 lines and 5 deps to remove.

## TIER 1 — Zero-Risk Deletions (done)

- [x] Remove `python-dotenv`, `pyyaml`, `markdown` from requirements.txt
- [x] Delete `interactive.py` (dead file)
- [x] Update `tests/test_package_structure.py` to remove `interactive.py` from expected modules
- [x] Remove dead imports (64 total found via `ruff check --select F401`: 62 auto-fixed, 2 manual):
  - `Protocol` in agents/__init__.py
  - `interactive.InteractiveDiscussion` import in main.py (module deleted)

## TIER 2 — Deduplication (done)

- [x] `_report_to_dict`: `AgentReport.to_dict()` added. Both orchestrator.py and orchestrator_deliberation.py use it.
- [x] `_CORRECTION_SYSTEM` / `_CORRECTION_USER`: Extracted to `ai/prompts_constants.py`, shared by client.py + ollama_provider.py.
- [x] JSON preprocessing pipeline: extracted to `ai/json_utils.py` (`JSONPipeline`), used by client.py + ollama_provider.py.
- [x] `run_review()` deprecated wrapper: Inlined to `run_deliberation()`. Tests updated.
- [x] `json.loads(json.dumps(defaults))` → `copy.deepcopy(defaults)` in cli.py.

## TIER 3 — ABC Removal (done)

- [x] `BaseOrchestrator(ABC)`: Inlined into `Orchestrator`. ABC methods removed.
- [x] `BaseProvider(ABC)`: Merged into `OllamaProvider`. `abstract_provider.py` removed.
  - `AIClient.complete()` KEPT: still used by cli.py `discuss` follow-up QA (not dead).

## TIER 4 — Config Cleanup (done)

- [x] Removed unused config keys from cli.py default dict.
- [x] Removed same keys from `settings.json`.

## TIER 5 — Debatable (flag only, do not delete)

- `feedback.py`: 4 methods dead in prod but tested (generate_feedback_prompt, etc.)
- `decision_tracker.py`: 2 methods dead in prod but tested
- `event_store.py`: 3 methods dead (load_from_disk, replay, clear)
- `knowledge_base.py`: 3 methods dead (ingest_text, get_context_for_query, delete_document)

## Test drift fixed (done)

Stale tests referenced the pre-refactor AgentReport schema (per-role attrs like
`capex_vs_opex`, `what_i_need_from_cto`). Schema now uses `verdict` + `extra_fields`.
Updated `tests/test_agent_report.py` and `tests/test_recent_changes.py` to the current
contract. All 10 pre-existing failures fixed.

## Verification

`pytest tests/ --ignore=tests/test_cli.py -q` → 331 passed, 1 skipped.
`ruff check --select F401 openexec/ src/ tests/` → clean.