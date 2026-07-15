---
format: 1920x1080
message: "OpenExec's board doesn't just agree with itself: hierarchical agent teams and research-grounded analysis produce real, defensible decisions — dissent included."
arc: Before (real dissent) → After-tease (the promise) → Bridge (product) → Step 1 (teams) → Step 2 (research grounding) → Wow (real resolution) → CTA
audience: developers evaluating an AI board-simulation CLI tool (README / landing-page embed)
mode: collaborative
---

## Video direction

- **Palette system** (from `frame.md`, never invented): `dark` register (ink-black `#111111` ground ·
  cream `#F0ECE5` text · fire-orange `#E85D26` sole accent) is the default, used on Frames 1, 2, 4, 5, 7
  — the "evidence" run. `orange` register (fire-orange ground · ink-black text) is reserved for the two
  brand-identity beats, Frame 3 and Frame 8, which bookend the video. Frame 6 uses the preset's own
  documented `Compare` treatment — a sanctioned DARK→ORANGE split within one frame, not a violation of
  "one register per frame." Never cream text on orange (absolute rule). No drop shadow, no rounded
  corners, no gradient ground, no second accent color, anywhere.
- **Motion grammar + reveal model**: long-tail `power3` settles throughout — no bounce / elastic /
  back.out anywhere in this video (a restrained brand register; no playful exception applies). **This
  video is silent (no narration, no music, no SFX — explicit user choice for this first cut).** With no
  VO to pace against, each frame's own **on-screen text cues** (already written in Step 3, or the
  content items themselves for Frames 4/6/7) stand in as the pacing reference: reveal each cue in its
  own window, spread across the shot, nothing dumped at t=0 — the same anti-PowerPoint discipline as a
  narrated video, cue-paced instead of VO-paced.
- **Rhythm / held-frame allocation**: Frames 2, 3, and 8 are the deliberate held/breather beats — short,
  calm, low-motion (Cover/Statement treatments are designed at "~45–55% silence" per `frame.md`).
  Frames 1, 4, 5, 6, 7 carry the active sequential reveals. This alternation is why Frame 3 (calm,
  orange) sits right after Frame 2 (calm, dark) — both breathe before Frame 4's more active build.
- **Negative list**: no drop shadow / rounded surface / gradient ground / serif companion / second
  accent (frame.md hard rules); no customer logos or vendor marks (none exist — nothing to render, not
  even a placeholder); no invented figures beyond the real `0.7` / `0.3` ratio and the real
  `board_report.md` text; no infinite/forever motion, no `Math.random` / `Date.now`; no slideshow
  front-load; no screensaver (independently-floating elements with no shared read).

## Frame 1 — Before

- scene: Bare canvas. Two lines of type land solo, one after the other.
- voiceover: ""
- duration: 7s
- transition_in: cut
- status: animated
- src: compositions/frames/01-before.html
- type: hook
- persuasion: Pain validation
- beat: tension
- blueprint: kinetic-type-beats (Adapt — Hook/escalation sub-shape, 2 beats not 3; keeps the
  hard-cut full-screen replace signature move)
- focal: n/a — no captured candidates, bespoke typography
- asset_candidates:

On-screen cues (silent, phrase-segmented for reveal):
1. "CTO disagreed."
2. "The board didn't flinch."

Real material: the CTO dissent from `board_report.md` on the microservices-migration
decision. Plain outcome language, no CLI/product jargon — per story-spine, the hook
must not open with subject-internal vocabulary.

Register: **dark** (Statement treatment — ink-black ground, cream text, lean left, one
clause inked fire-orange).

Scene 1 (0.0–3.0s): Solid ink-black ground. Cue 1 "CTO disagreed." hard-cut FLASH-in
dead-left (no fade/slide) — Barlow `h1` lowercase 900, cream. Camera static. →
`discrete-text-sequence`
Scene 2 (3.0–3.4s): Cue 1 clears by hard cut — the swap engine, no roll/scroll/blur. →
`discrete-text-sequence`
Scene 3 (3.4–7.0s): Cue 2 "The board didn't flinch." hard-cuts in, left-anchored,
Barlow `h1` lowercase; the word "flinch" inks fire-orange — the frame's one accent
clause. Settles and HOLDS to end; at most subtle jitter in the final ~1s. →
`discrete-text-sequence`

narrativeRole: establishes real stakes — a disagreement actually happened, and the
system didn't paper over it.
keyMessage: this isn't a yes-man.

## Frame 2 — After-tease (the promise)

- scene: The two hook lines clear; two new lines assemble in their place.
- voiceover: ""
- duration: 8s
- transition_in: crossfade
- status: animated
- src: compositions/frames/02-after-tease.html
- type: benefit_highlight
- persuasion: Future pacing
- beat: curiosity + relief
- blueprint: kinetic-type-beats (Reproduce — held/breather variant: per-word fade
  instead of Frame 1's hard-cut, for rhythm variety)
- focal: n/a — no captured candidates, bespoke typography
- asset_candidates:

On-screen cues:
1. "Because every executive has a real team behind them."
2. "And every claim is checked against real research."

This is the message landing — by story-spine's reverse-iceberg rule, the value
claim must arrive by beat 2. Everything from Frame 4 onward is evidence for this
claim, not new information.

Register: **dark** (Statement treatment, same as Frame 1 — continuity within the
two-frame "value" beat before the identity cut to Frame 3).

Scene 1 (0.0–3.5s): ink-black ground continues (crossfade from Frame 1's hold). Cue 1
enters via per-word staggered fade reveal — left-anchored Barlow `h2` lowercase cream;
the clause "real team" inks fire-orange. → `dynamic-content-sequencing`
Scene 2 (3.5–4.0s): Cue 1 clears via a gentle crossfade (softer than Frame 1's hard
cut — this is a held/breather beat). → `discrete-text-sequence`
Scene 3 (4.0–8.0s): Cue 2 enters via per-word staggered fade; "real research" inks
fire-orange. Holds to end, static; subtle jitter only in the final ~1.5s. →
`dynamic-content-sequencing`

narrativeRole: states the payoff before any mechanism is shown.
keyMessage: the promise — teams + grounding, not a single guessing agent.

## Frame 3 — Bridge (product)

- scene: The promise lines settle into a plain wordmark lockup, typography only.
- voiceover: ""
- duration: 7s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/03-bridge-product.html
- type: product_intro
- persuasion: Concrete specificity (naming the real mechanism instead of a vague promise — no bank persuasion tag fit cleanly, so this one is invented per story-design.md's allowance)
- beat: clarity
- blueprint: kinetic-type-beats (Reproduce — Product_Intro namedrop variant)
- focal: n/a — no captured candidates, bespoke typography
- asset_candidates:

On-screen cues:
1. "This is OpenExec."
2. "An AI board that argues for real reasons."

Section boundary into the evidence run — `zoom-through` per transition doctrine, and
the video's first **register switch** (dark → orange): a genuine state change, not
just a beat change, which is exactly what `zoom-through` is for.

Register: **orange** (Cover treatment — fire-orange ground, ink-black text, massive
lowercase `display` word, mono kicker, "Silence ~45%"). Held/breather beat.

Scene 1 (0.0–1.5s): fire-orange ground fills as the zoom-through cut arrives. A small
ink 1px rule stub + IBM Plex Mono uppercase kicker ("OPENEXEC — AI EXECUTIVE BOARD")
fades in top-left per Cover chrome. Camera static. → `discrete-text-sequence`
Scene 2 (1.5–4.0s): Cue 1 — "OpenExec" lands as a Barlow `display` (13cqw) lowercase
ink wordmark, left-anchored, hard-cut FLASH-in (Cover's massive-type focal move). →
`discrete-text-sequence`
Scene 3 (4.0–7.0s): Cue 2 enters beneath as a Barlow `lead` line at 75% ink opacity
(Cover's lead-line spec), per-word staggered fade. Holds to end — Cover's signature
restraint; at most subtle jitter. → `dynamic-content-sequencing`

narrativeRole: names the product plainly, no logo (none exists — see
asset-descriptions.md), right after the promise so the name attaches to a claim
already made, not the other way round.
keyMessage: OpenExec is the thing that does what Frame 2 just promised.

## Frame 4 — Step 1: teams

- scene: Four CXO nodes (CEO / CFO / CTO / CMO) appear, then each splits into its
  real named sub-agents with a connecting line animating upward into the CXO.
- voiceover: ""
- duration: 12s
- transition_in: crossfade
- status: animated
- src: compositions/frames/04-teams.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: clarity + control
- blueprint: compose (no bank shape fits a one-node-branches-into-several hierarchy
  build; `constellation-hub` is the near-miss but its camera push-in is nodes
  *converging on* a hub, the semantic opposite of a CXO branching *out* into a
  team. Composed from the motion vocabulary instead of forcing a wrong shape.)
- focal: n/a — no captured candidates, bespoke SVG/CSS org-chart
- asset_candidates:

Real content, exact names (source: `openexec/agents/__init__.py`, `TEAM_STRUCTURE`):
  CEO -> chief_of_staff, strategy_associate
  CFO -> financial_analyst, budget_planner, risk_analyst
  CTO -> engineering_lead, solutions_architect, sre
  CMO -> growth_marketer, content_strategist, seo_specialist

Register: **dark**. Layout: 4-column asymmetric grid, each column top-anchored with
the CXO name (Barlow `h3` lowercase cream) and its sub-agents beneath as IBM Plex Mono
uppercase labels, joined by animating 1px hairline (`border-dark`) connectors — no
gradient, no shadow, no rounded corners (system hard rules). The four CXO columns
double as this frame's "cues," each entering in its own window — nothing front-loaded.

Scene 1 (0.0–1.0s): ink-black ground; IBM Plex Mono uppercase kicker "HIERARCHICAL
TEAMS" fades in top-left. Nothing else on screen. → `discrete-text-sequence`
Scene 2 (1.0–3.5s): CEO column enters — "ceo" lands via short slide+fade into its slot,
then its 2 sub-agents ("chief_of_staff", "strategy_associate") cascade in beneath with
1px hairlines drawing upward into the CEO node. → `center-outward-expansion` +
`svg-path-draw`
Scene 3 (3.5–6.5s): CFO column enters the same way; its 3 sub-agents
("financial_analyst", "budget_planner", "risk_analyst") cascade in with hairline
connectors. → `center-outward-expansion` + `svg-path-draw`
Scene 4 (6.5–9.5s): CTO column enters; its 3 sub-agents ("engineering_lead",
"solutions_architect", "sre") cascade in with hairline connectors. →
`center-outward-expansion` + `svg-path-draw`
Scene 5 (9.5–12.0s): CMO column enters; its 3 sub-agents ("growth_marketer",
"content_strategist", "seo_specialist") cascade in. All four columns now co-resident;
the complete real hierarchy holds static to end, subtle jitter only. →
`center-outward-expansion` + `svg-path-draw`

narrativeRole: proves the "real team behind them" half of Frame 2's promise with
the actual hierarchy, not a stand-in diagram.
keyMessage: every CXO has real direct reports, by name.

## Frame 5 — Step 2: research proof (terminal)

- scene: A styled dark terminal window types out the real command, then reveals
  the real plain-text output lines one at a time.
- voiceover: ""
- duration: 12s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/05-terminal.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: confidence
- blueprint: typewriter-reveal (Adapt — Hook variant's live-typing signature move
  reproduced for the command, but the collapse-into-brand-payoff resolution is
  replaced with a hand-off into the real output lines, since this frame's job is
  proving the tool runs, not introducing the brand)
- focal: n/a — no captured candidates, bespoke terminal component
- asset_candidates:

Real content (verbatim):
  Command: openexec run "Should we migrate our monolith to microservices?" --teams --research --research-mix web=0.7,kb=0.3
  Output, revealed in order:
    Starting Simulation...
    => Targeted simulation: cto
    => Research grounding enabled -- web:0.7 / kb:0.3
    -> Report: board_report.md

`push-slide LEFT` continues the lateral "next beat" feel from Frame 4 — the second of
a two-beat consecutive feature-showcase run (teams, then research).

Register: **dark**. The terminal surface uses `ink-black-alt` (`#1A1A18`) with a 1px
`border-dark` border, sharp corners (no rounded surface, per system rule) — the
terminal chrome and the design system's flat aesthetic are the same thing here. IBM
Plex Mono throughout (the system's own mono chrome family).

Scene 1 (0.0–1.0s): ink-black ground; the terminal window fades/scales into place,
left-anchored, empty but for a blinking caret at the prompt. → `spring-pop-entrance`
(gentle, no overshoot) + `context-sensitive-cursor`
Scene 2 (1.0–5.0s): the real command types on character-by-character behind the caret.
Nothing else on screen. → `discrete-text-sequence` + `context-sensitive-cursor`
Scene 3 (5.0–6.0s): enter; caret drops a line; "Starting Simulation..." types on. →
`discrete-text-sequence`
Scene 4 (6.0–8.0s): "=> Targeted simulation: cto" reveals via hard-cut line-append
(faster than character typing — varies the pace so the full 12s isn't one typing
crawl). → `discrete-text-sequence`
Scene 5 (8.0–10.0s): "=> Research grounding enabled -- web:0.7 / kb:0.3" reveals the
same way; on arrival, a restrained fire-orange underline draws beneath "web:0.7 /
kb:0.3" to seed Frame 6's handoff. → `discrete-text-sequence` + `css-marker-patterns`
Scene 6 (10.0–12.0s): "-> Report: board_report.md" reveals; caret settles blinking at
the new prompt. Holds to end, static but for the caret blink and subtle jitter. →
`discrete-text-sequence`

narrativeRole: proves the tool is real and runnable — plain text, no color, no
markdown, matching the product's actual (intentional) CLI aesthetic.
keyMessage: this is a real command producing real output, not a mockup.

## Frame 6 — Step 2: research proof (ratio)

- scene: A proportioned two-panel split (70/30) states the real research-mix ratio —
  not an invented dial/gauge (the design system forbids the gradients and shadows a
  skeuomorphic dial would need; the preset's own `Compare` treatment is the honest fit).
- voiceover: ""
- duration: 8s
- transition_in: crossfade
- status: animated
- src: compositions/frames/06-research-mix.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: confidence
- blueprint: comparison-split (Adapt — keeps the signature move: two panels entering
  from opposite wings with mirrored 3D tilts, holding side-by-side; changes the
  panel WIDTHS from the blueprint's default equal split to an asymmetric 70/30,
  encoding the real ratio instead of a generic "X + Y together")
- focal: n/a — no captured candidates, bespoke split-panel component
- asset_candidates:

Real content: web:0.7 / kb:0.3 — directly continues from Frame 5's terminal line
("=> Research grounding enabled -- web:0.7 / kb:0.3"), same beat pair, hence the
tight `crossfade` (not a section-boundary transition).

Register: this frame IS `frame.md`'s documented **Compare** treatment (`argument ·
move: split + orange payoff · DARK→ORANGE`) — a sanctioned split, not a "one register
per frame" violation. Left panel (70% width, dark: ink-black ground / cream+orange
text). Right panel (30% width, orange: fire-orange ground / ink text — "ink-on-fire
is absolute", per frame.md). 1px divider between, per the treatment's own spec.

Scene 1 (0.0–0.8s): crossfade in from Frame 5, continuing the orange underline seeded
there; ink-black ground, panels not yet visible. → (transition-owned, no new rule)
Scene 2 (0.8–3.5s): left panel (70% width) enters from the left wing with a mirrored
3D book-open tilt, settles flush; IBM Plex Mono uppercase kicker "WEB SEARCH" fades in,
then the numeral "0.7" spring-pops in fire-orange beneath it. → `split-tilt-cards` +
`spring-pop-entrance`
Scene 3 (3.5–6.0s): right panel (30% width) enters from the right wing with the
opposing mirrored tilt, settles flush against the 1px divider; kicker "KNOWLEDGE BASE"
(ink-on-fire) fades in, then numeral "0.3" spring-pops in ink. → `split-tilt-cards` +
`spring-pop-entrance`
Scene 4 (6.0–8.0s): both panels hold side-by-side, static; one accent glow sweeps once
left-to-right across the 1px divider, then settles. Holds to end. →
`ambient-glow-bloom` (single pass)

narrativeRole: makes the "checked against real research" half of Frame 2's
promise legible as a real, user-configurable mechanism (`--research-mix`), not
a black box.
keyMessage: the ratio is a real flag the user sets, not marketing fuzz.

## Frame 7 — Wow: the resolution

- scene: The real board_report.md action items populate a vertical list, one at
  a time, each with its owner and timeframe.
- voiceover: ""
- duration: 12s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/07-resolution.html
- type: benefit_highlight
- persuasion: Show-don't-tell proof
- beat: triumph + relief
- blueprint: grid-card-assemble (Adapt — Benefits vertical-list signature move kept
  (co-resident accumulation, ~1 item/sec), but each line is skinned as a `Stat Grid`
  top-border card (1px hairline top, mono label) instead of a plain pill, since the
  content is structured — task / owner / timeframe — not a single value phrase)
- focal: n/a — no captured candidates, bespoke typography list
- asset_candidates:

Real content, verbatim from `board_report.md` (Final Priority Actions):
  1. Define the phased migration blueprint (MVP scope) — Owner: CTO — 1 Week
  2. Finalize resource allocation for observability tooling — Owner: CFO — 3 Days
  3. Schedule a mandatory decision meeting on integration strategy — Owner: CEO — 48 Hours

Section boundary from evidence into resolution/close — `zoom-through`. Exactly three
items — matches frame.md's own "cap bullets at three" rule with the real count, no
padding needed.

Register: **dark**. Owner + timeframe render in IBM Plex Mono fire-orange (the
frame.md "orange numerals" convention, applied to these figures instead of literal
numerals — the closest honest fit, since these are the frame's real, load-bearing data).

Scene 1 (0.0–1.0s): ink-black ground; IBM Plex Mono uppercase kicker "FINAL PRIORITY
ACTIONS" fades in top-left. → `discrete-text-sequence`
Scene 2 (1.0–4.5s): first card enters via short slide+fade into its slot (top-border
hairline only): "Define the phased migration blueprint (MVP scope)" in Barlow `body`
cream, "Owner: CTO" / "1 Week" in IBM Plex Mono fire-orange beneath. →
`center-outward-expansion` (short-path slide-into-slot) + `spring-pop-entrance`
Scene 3 (4.5–8.0s): second card enters beneath, co-resident (first card stays fully
lit — accumulating, not dimming): "Finalize resource allocation for observability
tooling" / "Owner: CFO" / "3 Days". → `center-outward-expansion` + `spring-pop-entrance`
Scene 4 (8.0–11.0s): third card enters: "Schedule a mandatory decision meeting on
integration strategy" / "Owner: CEO" / "48 Hours". All three now co-resident. →
`center-outward-expansion` + `spring-pop-entrance`
Scene 5 (11.0–12.0s): all three hold, static, full read; subtle jitter only. →
settle-and-hold

narrativeRole: resolves Frame 1's dissent — the disagreement didn't stall the
board, it produced three owned, dated actions.
keyMessage: dissent went in, concrete accountable actions came out.

## Frame 8 — CTA

- scene: A plain typographic wordmark lockup with a closing line underneath.
- voiceover: ""
- duration: 6s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/08-cta.html
- type: cta
- persuasion: (direct close, no scarcity/urgency tag needed)
- beat: motivation
- blueprint: cta-morph-press (Adapt — keeps the signature "resting mark settles at
  center" beat; drops the cursor-arrival-and-click scenes from the bank template,
  since there is no clickable in-video CTA button — the ask is "go read the README",
  not a UI click)
- focal: n/a — no captured candidates, bespoke typography
- asset_candidates:

On-screen cues:
1. "OpenExec"
2. "Real teams. Real research. Real decisions."

No install command is shown — an unverified package name would be an invented
fact, which the brief explicitly rules out. The wordmark alone is the close;
the README this embeds in already carries install instructions.

Register: **orange** (Cover treatment — bookends Frame 3). Held/breather beat.

Scene 1 (0.0–2.0s): zoom-through arrival lands on fire-orange ground; cue 1
"OpenExec" resolves dead-center as a Barlow `display` (13cqw) lowercase ink wordmark
— the same Cover treatment as Frame 3, bookending it. A faint rotational-only resting
breath is the only motion. → `spring-pop-entrance` (arrival) + `sine-wave-loop`
(low-amplitude resting breath)
Scene 2 (2.0–4.5s): cue 2 types on beneath the wordmark, IBM Plex Mono uppercase,
three short clauses with a brief hard-cut pause between each — matching the video's
own three-part promise (teams / research / decisions). → `discrete-text-sequence`
Scene 3 (4.5–6.0s): holds, static, dead-center, to the end — the only "exit" is the
video ending on the held wordmark (per the seek-safe core: only the final frame gets
a real exit). → settle-and-hold

narrativeRole: closes on brand identity, not an unverifiable claim.
keyMessage: OpenExec, plainly.
