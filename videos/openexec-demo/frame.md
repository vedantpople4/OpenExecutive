---
format: 1920x1080
palette:
  bg: "#0A130F"
  bg_panel: "#0F1B15"
  fg: "#ECEFEA"
  fg_dim: "#8A9690"
  accent: "#34C77B"
  hairline: "#20302A"
typography:
  display: "Oswald"
  display_weight: 700
  mono: "JetBrains Mono"
  mono_weight_body: 400
  mono_weight_strong: 700
spacing:
  unit: 8
  corner_radius: 0
components:
  terminal_window:
    chrome: "3-dot traffic light, hairline top rule, no drop shadow"
    corner_radius: 0
    border: "1px solid var(--hairline)"
---

## Overview

A developer-facing CLI demo, not a brand-story promo. The subject is the real
`openexec` tool: a working terminal, real config, real command, real streamed
agent output, real `board_report.md`. Nothing here borrows the palette, type,
or story shape of any other video in this repo — this is a fresh identity for
a fresh video, built for the terminal-capture genre (dev-tool screen demo),
not the typographic-statement genre.

## The Frame

- **Ground:** `#0A130F` — near-black, tinted toward the accent's green hue
  (never a dead/neutral `#000`). This is the one background used across every
  scene; no gradient ground, no second background color.
- **Panel:** `#0F1B15` — a barely-lighter surface reserved for the terminal
  window / card chrome, so the terminal reads as an object sitting on the
  ground, not the ground itself.
- **Foreground text:** `#ECEFEA` — paper-white tinted cool/green, never pure
  `#FFFFFF`.
- **Dim foreground:** `#8A9690` — for secondary terminal text (labels,
  timestamps, comments, prompts) — a real terminal has text-hierarchy inside
  itself; this token is that hierarchy, not a second accent.
- **Sole accent:** `#34C77B` — a muted, institutional emerald (deliberately
  not neon `#00FF00` — this is a product demo, not a hacker-movie pastiche).
  Used for: the one CLI success glyph/prompt caret, the one on-screen label
  per scene that names what's happening, and the final CTA. Never used for
  large fills — accent is ink, not wallpaper.
- **Hairline:** `#20302A` — 1px rules only. No drop shadow anywhere, no
  rounded corners anywhere (`corner_radius: 0` — a terminal window is a hard
  rectangle).

## Typography

- **Display (scene titles / CTA / captions-of-intent):** Oswald, weight 700,
  uppercase or sentence-case per scene, tight tracking. Condensed sans reads
  as "product UI chrome" — distinct register from the terminal's monospace.
- **Terminal / data / code / config:** JetBrains Mono. Weight 400 for
  streamed body text, 700 only for the literal prompt line the user "typed"
  and for section headers inside `board_report.md` excerpts. This is the
  file's real voice — every line of mono text in this video is copied
  verbatim from an actual `openexec` run, never invented.
- Pairing is sans (Oswald) + mono (JetBrains Mono) — never two sans, per
  typography guardrails. The tension: Oswald is the product's confident
  outer voice; JetBrains Mono is the tool's literal, unfiltered inner voice
  (the actual bytes it prints). That contrast — polished claim vs. raw
  proof — is the whole point of a dev-tool demo.
- Sizes are full-screen/YouTube scale: headlines 60px+, terminal body no
  smaller than 22px (legible at video scale, not IDE scale).

## Motion

- Long-tail `power2`/`power3` settles; no bounce/elastic anywhere — a
  terminal does not bounce.
- Terminal text reveals as authentic incremental output (line-by-line /
  monospace character reveal at a readable clip), not a generic fade-in —
  the reveal mechanic IS the content (this is what streaming looks like).
- Scene transitions are hard cuts or short crossfades on the terminal frame
  itself; no wipes, no slides — keep the camera/frame static so the eye
  trusts the terminal as a real, continuous session.
- Background layer: one hairline grid (very low opacity, static or barely
  breathing) behind the terminal panel — enough depth to not read as a flat
  web page, restrained enough to not compete with real text.

## Negative list

- No gradient ground, no second accent hue, no neon/cyan-purple defaults.
- No drop shadow, no rounded corners, no card-grid decoration.
- No invented terminal output, no invented config values, no invented
  agent dialogue — every mono-font line in this project is sourced from a
  real captured `openexec` run or a real file in this repo (`settings.json`,
  `config/openexec.yaml`, `board_report.md` excerpts).
- No shared assets, palette, fonts, or story beats from any other video
  project in this repo — this identity is standalone.
