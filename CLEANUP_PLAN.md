# OpenExec Cleanup Plan

> Based on `ponytail:ponytail-audit` — 22 findings, ~500 lines and 5 deps to remove.

## TIER 1 — Zero-Risk Deletions (in_progress)

- [x] Remove `python-dotenv`, `pyyaml`, `markdown` from requirements.txt
- [x] Delete `interactive.py` (dead file)
- [x] Update `tests/test_package_structure.py` to remove `interactive.py` from expected modules
- [ ] Remove dead imports (25 total, 6 confirmed):
  - `tqdm` in orchestrator_deliberation.py
  - `os`, `Set` in knowledge_base.py
  - `ABC`, `abstractmethod` in agents/interface.py
  - `datetime`, `Optional` in orchestrator.py
  - ...and remaining 18 from full audit

## TIER 2 — Deduplication (pending)

- [ ] `_report_to_dict`: Add `to_dict()` to `AgentReport` dataclass. Replace 2 copies in orchestrator.py and orchestrator_deliberation.py.
- [ ] `_CORRECTION_SYSTEM` / `_CORRECTION_USER`: Extract to shared module, remove duplicates from client.py + ollama_provider.py.
- [ ] JSON preprocessing pipeline: ~180 lines copy-pasted between ai/client.py and ai/ollama_provider.py. Extract to `ai/json_utils.py`.
- [ ] `run_review()` deprecated wrapper: Inline to `run_deliberation()`. Update tests.
- [ ] `json.loads(json.dumps(defaults))` → `copy.deepcopy(defaults)` in cli.py.

## TIER 3 — ABC Removal (pending)

- [ ] `BaseOrchestrator(ABC)`: Inline into `Orchestrator`. Remove ABC methods. Update `__init__.py` exports.
- [ ] `BaseProvider(ABC)`: Merge into `OllamaProvider`. Remove abstract_provider.py. Update AIClient type hint.
- [ ] `AIClient.complete()`: Remove passthrough. Callers only use `complete_json/complete_json_with_retry`.

## TIER 4 — Config Cleanup (pending)

- [ ] Remove 7 unused config keys from cli.py default dict: `ai.provider`, `agents.analysis_depth`, `agents.confidence_threshold`, `agents.max_interactions`, `output.format`, `output.include_sections`, `simulation.phases`.
- [ ] Remove same keys from `settings.json`.

## TIER 5 — Debatable (flag only, do not delete)

- `feedback.py`: 4 methods dead in prod but tested (generate_feedback_prompt, etc.)
- `decision_tracker.py`: 2 methods dead in prod but tested
- `event_store.py`: 3 methods dead (load_from_disk, replay, clear)
- `knowledge_base.py`: 3 methods dead (ingest_text, get_context_for_query, delete_document)

## Verification

After each tier: `pytest tests/ --ignore=tests/test_cli.py -q`
