# OpenExec — Code Progress Handoff

**Last updated:** 2026-08-20
**Base version (LinkedIn):** `e65d2e6` (2026-07-18 CLI demo video)
**Current head:** `604a82d` (main, pushed) + 1 uncommitted change (see below)

---

## What shipped since the LinkedIn version

59 commits. The repo went from **a working demo to an investor-ready prototype**.

### New user-facing commands (6)
| Command | What it does |
|---|---|
| `compare` | Diff two runs: consensus/dissent shifts, action-item deltas, risk changes, per-agent alignment |
| `register` | Dashboard of all stored decisions: totals, recurring risks, alignment trends, monthly activity |
| `demo` | Canned board run — **no LLM required**; narrates the deliberation step by step (`Step 1`…`Step 6`: CEO frames it, CFO/CTO stake positions, specialist analysis, CEO synthesis, board decision assembled, reports written), then writes a real report + HTML in under 2 seconds. `--no-steps` skips the narration for scripting. |
| `render` | Any stored decision → standalone board-ready HTML. **Was completely broken** until this session — see "Bug found & fixed" below — now works and is regression-tested. |
| `history` / `review` / `search` | Now show actual verdicts, action items, and risks (previously just prompts) |

### New capabilities
- `--dry-run` cost + ETA (config-driven `price_per_call` / `seconds_per_call`)
- `--html` flag on `run` → self-contained, shareable report
- `demo` step-by-step deliberation narration (see table above) — same canned fixture, zero LLM/network calls either way
- 6 dead-core modules removed; `tqdm` dependency dropped; `_id_from_name` hash helper deduped

### Reliability & correctness (14+ fixes)
- Provider retries on all request errors; reasoning-only responses treated as failure
- Memory context actually reaches the LLM; repeated prompts update in place (no dupes)
- KB ingestion idempotent; verdict flattening fixed; `--agents` validation; CEO gated on active agents
- `--no-memory` now actually blocks storage (was gated on the wrong flag — `--no-feedback`)
- **`render` command registered.** A malformed comment block (`# ==============================@app.command()` on one line) had swallowed the `@app.command()` decorator into a comment, so `render` was defined but never wired to Typer — silently absent from `--help`, every invocation failed with `No such command 'render'`. Found by manually exercising every promised command end-to-end rather than trusting the code looked right. Fixed; regression-tested (see below).
- `run --dry-run` no longer prints "Starting Simulation..." before the estimate (banner moved past the dry-run short-circuit)

### Engineering & trust
- **GitHub Actions CI** — ruff + pytest on Python 3.10/3.12/3.14, coverage gate (**97%** on the value surface: `main`, `risk_analyzer`, `grounding`, `export`, `event_store`), secrets scan
- **Tests: 18 → 442** (24×), including a full mock-provider pipeline suite (`tests/test_run_integration.py`, 9 tests) and a dedicated `render` regression suite (`tests/test_render_cli.py`, 3 tests — deliberately outside `test_cli.py` so it actually runs in CI)
- **Repo hygiene for public launch** — runtime data, local settings, and secrets untracked; `settings.example.json`; prompt-injection guard on data files

---

## Test & quality state

```
442 passed, 1 skipped   (pytest tests/ --ignore=tests/test_cli.py)
ruff clean
coverage: 97.38%+ (gate: 70%)
```

**Why test_cli.py is excluded from CI:** it hits the live-LLM path (`main()` with real `AIClient()`), which hangs without a local model. The full pipeline is now exercised headlessly by `tests/test_run_integration.py` via a `MockAIClient`.

### The mock-provider suite (tests/test_run_integration.py)
Exercises the complete `openexec run` pipeline against canned JSON (no network):
- inception → analysis → deliberation → synthesis → report → events → decision-log
- `--html`, `--research`, `--teams`, `--no-memory` flags
- asserts the report contains the board decision, not fallback stubs

---

## Completed this session (2026-08-14 → 2026-08-20)

### HyperFrames video — `videos/openexec-improvements/`
Feature-reveal promo highlighting the improvements above.
- **Route:** `/product-launch-video` (concept: "The Investor's 5 Minutes")
- **Brief:** 16:9, ~40s, text-led (no VO), storyboard reviewed, 7 frames
- **Design pivot:** initially built against a generic warm cream/coral "Claude" preset, then
  fully **restyled to match `videos/openexec-demo`'s terminal identity** (`#0A130F` bg /
  `#0F1B15` panel / `#ECEFEA` fg / `#8A9690` dim / `#34C77B` accent / `#20302A` hairline;
  Oswald 700 + JetBrains Mono; `corner_radius: 0`; no drop shadows; no bounce/elastic easing)
  per explicit user direction, so the two videos read as one series. `frame.md` and
  `STORYBOARD.md` updated to document this as an intentional, explicit exception to
  `openexec-demo/frame.md`'s own "standalone identity, don't reuse" note.
- **Pacing fix:** frame 4 (HTML export) originally sat on a bare white/dark card for ~1.5s
  before any content appeared (~30% of a 5s frame) — content now overlaps the URL-typing
  beat instead of waiting for it, landing within ~0.3–1.3s. Frame 3 tightened similarly.
- **Status: done.** All 7 frames built, `npm run check` clean (0 errors, 40/40 WCAG AA
  contrast checks pass), rendered to
  `renders/openexec-improvements_2026-08-14_20-11-44.mp4` (1920×1080, h264, 30fps, exactly
  40.0s, zero ffmpeg decode errors across the full file). Opened and confirmed playing
  correctly. Not published (user opted to keep it local).
- This directory is currently untracked (`?? videos/openexec-improvements/`).

### CLI fixes, found by actually running every promised command
Prompted by "the work promised in the demo should also be tested" — went through every
command in the What-Shipped table above against a real local LLM (LM Studio,
`google/gemma-4-e2b` at `127.0.0.1:1234`), not just the mock suite:
- `demo`, `run --dry-run`, `run --html` (real 5-round deliberation, real board decision,
  correctly appeared in `history`), `history`, `review`, `search`, `register`, `compare` —
  all verified working against real stored decisions.
- **Found `render` was completely broken** (see Reliability fixes above) — never appeared in
  `--help`, every invocation failed. Fixed and added `tests/test_render_cli.py` (3 tests, CI-covered).
  Verified the tests actually catch the regression: reverted the fix, watched 2/3 fail, restored
  it, watched all pass.
- Committed as `604a82d`.

### `demo` step-by-step narration (uncommitted)
`openexec demo` now walks through the canned deliberation step by step (`Step 1`…`Step 6`)
instead of jumping straight to the written report — same `demo_fixture.py` data, just narrated
in order with ~0.15–0.25s pacing between lines so it reads like a live run. Added
`_print_demo_steps()` / `_demo_step()` / `_demo_line()` helpers in `openexec/cli.py` and a
`--steps/--no-steps` flag (defaults on; `--no-steps` skips straight to file output for
scripting). Zero LLM/network calls either way; still completes in under 2 seconds.
Verified: 442 tests pass, ruff clean. **Not yet committed** — `git status` shows
`M openexec/cli.py`.

### LinkedIn post drafted
Announcement post for this upgrade cycle (callback to the "last time you saw a demo" framing
from the video's own hook), covering the demo narration, the 6 new commands, `--dry-run`,
and the RAG/grounding layer. Iterated per feedback (cut the test-count paragraph, added
hashtags + more AI/ML terminology) to a final version the user copied out. Not saved to a
file in the repo — text-only, lives in this chat's history if it needs to be regenerated.

---

## Remaining / open

- **Commit the `demo` step-by-step narration** (`openexec/cli.py` uncommitted change above).
- **`test_cli.py`** — still hangs on the live-LLM path in CI. The mock suite covers the wiring it was supposed to. Genuinely live-LLM testing remains a gap (needs a model running in CI or a record-replay fixture). Not scoped this session — flagged as an accepted gap, not a pending fix.
- **`render`/`compare` path resolution** stays permissive by design (read-only, user-owned files).
- **Video not published** — rendered locally only, per user's explicit choice; `npm run publish` would produce a shareable link if wanted later.

---

## How to verify the current state

```bash
ruff check openexec/ tests/
pytest tests/ --ignore=tests/test_cli.py -q
pytest tests/ --ignore=tests/test_cli.py -q --cov=openexec.main --cov=openexec.risk_analyzer --cov=openexec.grounding --cov=openexec.export --cov=openexec.event_store --cov-fail-under=70

# Spot-check the two things fixed/added this session by hand:
openexec demo                 # step-by-step narration, Step 1..6, no LLM
openexec render 1 -o /tmp/r.html && open /tmp/r.html   # was "No such command" before the fix
```
