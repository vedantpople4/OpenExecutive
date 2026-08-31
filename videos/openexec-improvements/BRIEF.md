---
workflow: product-launch-video
flow: automation
storyboard: yes
message: "OpenExec went from a working demo to an investor-ready prototype — see it work in 5 minutes with no LLM required"
destination: linkedin-feed
aspect: 1920x1080
language: en
length: 45s
angle: investor-walkthrough
---

## Intent

A feature-reveal promo for OpenExec (CLI tool simulating a CEO/CFO/CTO/CMO board
debate on a business decision), highlighting everything that changed since the
version shown in the previous LinkedIn post (the literal CLI demo).

Chosen concept — "The Investor's 5 Minutes": a paced, text-led walkthrough of
what a stakeholder can see in five minutes with no model installed. `openexec demo`
(runs a canned board decision with zero LLM setup) → the generated `board_report.md`
→ the standalone `--html` report. The improvements are revealed through what the
tool now actually produces. Text-led, no voiceover: kinetic type + captions carry it.

Improvements to highlight (since the LinkedIn/video version):
- 6 new commands: compare, register, demo, render, history/review/search (real verdicts, not just prompts)
- --dry-run cost + ETA, --html flag
- 440 tests (was 18), CI-gated, coverage gate, secrets scan
- repo hygiene: runtime data + local settings untracked, settings.example.json
- reliability: provider retries, memory fixes, prompt-injection guard
- demo mode: a canned board decision with no LLM

## Assets

- Real `openexec demo` run: `demo_board_report.md` + `demo_board_report.html` generated from the actual tool (no-capture path; this is a CLI, nothing to crawl).
- Real command output: `openexec --help` command list, `--dry-run` output, `history`/`register` output.

## Customizations

- Text-led, no VO (user choice) — captions/kinetic type carry the story.
- Concept rides: terminal/captured-report reveal + stat count-up (440 tests).

## Notes

- Destination LinkedIn feed → 16:9 per user choice.
- ~45s per user choice.
- Storyboard review first (user choice) — review plan + wireframes on the board before the full build.
- Auth: HeyGen not signed in — continuing offline (local engines); text-led video needs no TTS.
