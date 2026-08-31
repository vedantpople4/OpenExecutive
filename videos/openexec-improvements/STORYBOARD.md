---
format: 1920x1080
message: "OpenExec went from a demo to an investor-ready prototype — see it work in 5 minutes, no LLM required"
arc: Future Pacing — imagine the new state → name what changed → proof
audience: investors, founders, and technical stakeholders on LinkedIn
mode: collaborative
music: confident, understated — warm minimal pulse, no percussion lead
---

## Frame 1 — Hook: the last time you saw it

- scene: A single statement builds word by word: "The last time you saw OpenExec… it was a demo."
- duration: 5s
- poster: 2s
- transition_in: cut
- status: built
- voiceover: "The last time you saw OpenExec, it was a demo."
- src: compositions/frames/01-hook.html
- type: hook
- persuasion: Negative contrast
- beat: curiosity
- blueprint: kinetic-type-beats
- asset_candidates:

Open cold on the change. The previous LinkedIn video showed a literal CLI demo; this frame names that gap and promises the upgrade. Kinetic type swaps tokens in place ("a demo" → the payoff line later).

## Frame 2 — The demo, zero setup

- scene: Terminal surface with `openexec demo` typed, then the report file appears.
- duration: 6s
- transition_in: zoom-through
- status: built
- voiceover: "Now it works in five minutes — no LLM, no config, no signup."
- src: compositions/frames/02-demo.html
- type: product_intro
- persuasion: Friction reduction
- beat: ease + control
- blueprint: cursor-ui-demo
- asset_candidates: assets/dry_run.txt — dry-run estimate output; assets/demo_board_report.md — the generated report

The dark terminal window (matched to `../openexec-demo`'s identity) carries `openexec demo`. A cursor types the command; the terminal fills with the generated report filenames. The "no LLM required" line lands as an accent-green mono kicker.

## Frame 3 — The report is real

- scene: The actual board report renders — summary, consensus, dissent, action items — section by section.
- duration: 6s
- transition_in: push-slide LEFT
- status: built
- voiceover: "The board commits to the integration path — a real decision you can act on."
- src: compositions/frames/03-report.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: confidence + clarity
- blueprint: video-text-pivot
- asset_candidates: assets/demo_board_report.md — full board report markdown

The real `demo_board_report.md` content — Executive Summary, Board Decision, Consensus, Action Items — reveals section by section as kinetic cards on the cream ground. This is the artifact, not a mockup.

## Frame 4 — Take it to the board

- scene: The report card pivots to a browser-style surface holding the standalone HTML report.
- duration: 5s
- transition_in: blur-crossfade
- status: built
- voiceover: "One flag later, it's a standalone report you can send to a board."
- src: compositions/frames/04-html.html
- type: benefit_highlight
- persuasion: Friction reduction
- beat: ease + readiness
- blueprint: device-surface-showcase
- asset_candidates: assets/demo_board_report.html — standalone HTML report

The `--html` flag's output shown as a clean browser surface — a self-contained, shareable document. Warm-navy window chrome, hairline elevation.

## Frame 5 — The new commands

- scene: Command names populate a grid one at a time: compare, register, render, history, review, search.
- duration: 7s
- transition_in: push-slide RIGHT
- status: built
- voiceover: "Six new commands — compare, register, render, history, review, search."
- src: compositions/frames/05-commands.html
- type: feature_showcase
- persuasion: Value stacking
- beat: control + empowerment
- blueprint: grid-card-assemble
- asset_candidates: assets/help.txt — the 22-command help list; assets/compare.txt — run-to-run diff output

A tasteful grid of mono command names assembles on cream. Each maps to a one-line benefit underneath (compare = "see the board change its mind"). No clutter — six cards, one idea each.

## Frame 6 — Run it before you run it

- scene: `openexec run "…" --dry-run` output: "Estimated LLM calls: 9-15 · Estimated time: 3m-5m".
- duration: 5s
- transition_in: crossfade
- status: built
- voiceover: "Know the cost and the time before you spend a token."
- src: compositions/frames/06-dryrun.html
- type: benefit_highlight
- persuasion: Risk reversal
- beat: control + confidence
- blueprint: typewriter-reveal
- asset_candidates: assets/dry_run.txt — dry-run estimate output

A quiet terminal frame — the dry-run line types in, the call/time estimate lands. Anchor frame for the "cost + ETA" improvement.

## Frame 7 — CTA

- scene: Sign-off statement resolves onto the repo: "See it work in five minutes." + `openexec demo`.
- duration: 6s
- transition_in: zoom-through
- status: built
- voiceover: "See it work in five minutes — clone the repo, run openexec demo."
- src: compositions/frames/07-cta.html
- type: cta
- persuasion: Future pacing
- beat: motivation + inevitability
- blueprint: logo-assemble-lockup
- asset_candidates:

The one coral callout moment on the final frame: "See it work in 5 minutes." The command `openexec demo` sits beneath in mono, and the repo renders as a hairline text lockup. Cream ground, one coral voltage.
