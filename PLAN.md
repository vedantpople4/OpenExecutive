# OpenExec Prototype-Readiness Plan

Goal: turn OpenExec into a prototype an investor can *see work in 5 minutes*
and a real user can adopt in one session — not just a repo with passing tests.

Status: Phases 0-5 shipped (2026-08-10). Open items marked "remaining".

## Hard evidence (from /health + repo audit)

- Coverage 54% overall. `main.py` (the report renderer, *the deliverable*) 1%,
  `risk_analyzer.py` 13%, `grounding.py` 23%, `export.py` 29%, `event_store.py` 33%.
- CI excludes `tests/test_cli.py` — the live-LLM path is never tested anywhere.
- Git tracks runtime data that `.gitignore` already excludes:
  `decisions/` (19), `memory/` (18), `knowledge_base/` (3), `.claude/settings.local.json`
  (leaks absolute home paths), `settings.json` (has `api_key` field), `graphify-out/` (32),
  plus 42 `videos/` files. `.git` is 20MB.
- No demo/playback path: an investor cannot run the tool without standing up a
  local LLM server. That is the T0 blocker.
- No secrets scan in CI. `api_key` field sits in a tracked `settings.json`.

## Phase 0 — Repo hygiene (do first; investor-proof the repo)

- `git rm --cached` tracked runtime data: `decisions/`, `memory/`,
  `knowledge_base/`, `graphify-out/`, `.claude/settings.local.json`.
- Commit a `settings.example.json`; gitignore `settings.json` (keep empty api_key
  out of history going forward). Update `tests/test_cli.py` settings tests + the
  `setup`/`run` "settings.json not found" UX to point at the example.
- Replace the `.claude/settings.local.json` tracked copy with a gitignored default.
- Add a lightweight secrets scan step to CI (grep-based, zero deps) so api keys
  can't land in future commits.
- Keep the two demo MP4s; drop the promo video dir (fonts, captures) from tracking
  unless it's the README embed.

## Phase 1 — Coverage push on the value surface (pure, no LLM)

- `tests/test_main.py`: every `write_report` section — board decision, consensus/
  dissent, fallback warnings, grounding line, risk matrix, action items. `main.py`
  currently 1%; this is the artifact users act on.
- `tests/test_risk_analyzer.py`: `quantify_risk` banding, priority, matrix layout.
- `tests/test_grounding.py`: numeric-claim extraction + grounding counts.
- `tests/test_export.py`: csv/markdown/json writers.
- `tests/test_event_store.py`: append + persistence round-trip.
- CI gains a coverage gate (`--cov=openexec --cov-fail-under=65`) so the bar sticks.

## Phase 2 — Investor demo mode (the magic moment)

- `openexec demo` — runs a *canned* stored decision end-to-end: reads a fixture
  `results` dict, emits `board_report.md` + HTML, no LLM required. Investors get
  the full artifact in seconds with zero setup.
- `openexec demo` reuses `report_html` + `write_report` so it demos the real
  renderer, not a stub.
- Pair with `--dry-run` (cost/ETA) to show the "before" decision too.

## Phase 3 — DX / onboarding polish

- `openexec --help` and `run --help` must narrate the 6 newer commands
  (`compare`, `render`, `register`, `history`, `review`, `search`).
- First-run: `run` without `settings.json` prints the exact 3-step fix
  (already decent — tighten to reference `settings.example.json`).
- README: add a 60-second "see it now" block pointing at `openexec demo`.

## Phase 4 — CI + security hardening

- Coverage gate (Phase 1).
- Secrets scan step (Phase 0).
- Re-add a mock-provider `run` integration test (the current gap that
  `test_cli.py` skips) so the full pipeline is exercised headlessly.

## Phase 5 — /cso security pass

- Full CSO audit: secrets archaeology, dependency supply chain, prompt-injection
  surfaces (data files ingested into prompts), and the new HTML/export paths.
- Fix anything concrete it surfaces (injection escaping, file-path validation on
  `render`/`compare` refs).

## Risks / problems that may arise

1. **Decision data in git history already** — `git rm --cached` stops the bleed
   but history retains old copies. For a public repo, decide whether to rewrite
   history (`git filter-repo`) or accept it (data is synthetic test runs; verify).
2. **`settings.json` required at runtime** — if we gitignore it, fresh clones
   break on `run` until `setup`/copy-from-example runs. The error path must say
   exactly that. Risk: a user ignores the message and reports "broken".
3. **Coverage gate flakiness** — `--cov-fail-under` fails CI on unrelated
   drift. Mitigate: gate on `main.py`, `risk_analyzer.py`, `grounding.py`,
   `export.py` specifically, not the whole package at once.
4. **Demo fixture drift** — a canned `results` dict can silently diverge from the
   real orchestrator output shape. Mitigate: `demo` validates required keys and
   reuses the *same* `write_report`/`report_html` as production.
5. **Prompt injection via `data/`** — arbitrary files are ingested into prompts;
   a malicious corpus could hijack agents. `sanitize_prompt` covers user text, not
   data files. CSO should confirm the boundary.
6. **`render`/`compare` path traversal** — refs resolve files under `decisions/`;
   verify a crafted ref can't escape the directory (Path normalization).

## Definition of Done

- `openexec demo` produces a real report + HTML with no LLM.
- Coverage on main/risk/grounding/export/event_store ≥ 80% each; CI gate enforces.
- Repo clean: no runtime data, local settings, or secrets tracked; secrets scan
  green in CI.
- `--help` narrates every command; README has a 60-second demo path.
- CSO pass complete, findings fixed or explicitly deferred.
- Full suite green (incl. mock-provider integration test), ruff clean.

## Status (2026-08-10)

- **Phase 0 shipped** — runtime data, local settings, and promo video untracked;
  `settings.example.json` added; `.gitignore` covers `settings.json` +
  `.claude/*`; secrets scan step added to CI; `settings.json not found` UX
  references the example.
- **Phase 1 shipped** — 76 new tests across `test_main`, `test_risk_analyzer`,
  `test_grounding`, `test_export`, `test_event_store`. Coverage: `main.py` 1→77%,
  `risk_analyzer` 13→97%, `grounding` 23→100%, `export` 29→100%, `event_store`
  33→97%. CI coverage gate at 70% on the value surface.
- **Phase 2 shipped** — `openexec demo` renders a canned board decision to
  markdown + HTML with no LLM; `tests/test_demo.py` guards the fixture against
  renderer drift.
- **Phase 3 shipped** — `demo` surfaced first in `--help`; README has a
  "see it work in 5 seconds" Quick Start block.
- **Phase 5 shipped** — data-corpus prompt injection guarded (untrusted-data
  framing + `<document>` wrappers); git-history secrets scan clean; HTML
  escaping + `render`/`compare` write paths verified.
- **Remaining** — full mock-provider `run` integration test (CI still excludes
  `test_cli.py`); `render`/`compare` path resolution stays permissive by design
  (read-only, user-owned files).
