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
    chrome: "3-dot traffic light (outline only, no fill), hairline top rule, no drop shadow"
    corner_radius: 0
    border: "1px solid var(--hairline)"
---

## Overview

This is a sequel/companion video to `../openexec-demo` (the prior LinkedIn CLI
demo). By explicit user direction, this project **deliberately reuses that
video's identity** — same palette, same typography, same terminal-window
construction, same motion restraint — so the two videos read as one series.
(`openexec-demo/frame.md` frames itself as a standalone identity not meant to
be borrowed elsewhere; that rule is overridden here on purpose for series
continuity. Do not further propagate this palette to unrelated projects
without the same explicit instruction.)

## The Frame

- **Ground:** `#0A130F` — near-black, tinted toward the accent's green hue.
  One background across every scene; no gradient ground.
- **Panel:** `#0F1B15` — barely-lighter surface for terminal windows/cards,
  so a panel reads as an object sitting on the ground, not the ground itself.
- **Foreground text:** `#ECEFEA` — paper-white tinted cool/green, never pure
  `#FFFFFF`.
- **Dim foreground:** `#8A9690` — secondary text (labels, kickers, dim output
  lines).
- **Sole accent:** `#34C77B` — muted institutional emerald. Used for: command
  text, success glyphs, the one on-screen label naming what's happening per
  scene, and CTA lines. Never a large fill.
- **Hairline:** `#20302A` — 1px rules only. No drop shadow anywhere, no
  rounded corners anywhere (`corner_radius: 0`).

## Typography

- **Display** (scene titles / CTA / kinetic-type beats): Oswald, weight 700.
- **Terminal / data / code:** JetBrains Mono, weight 400 body / 700 for
  prompt lines and command names.
- Pairing is sans (Oswald) + mono (JetBrains Mono) — never two sans.

## Motion

- Long-tail `power2.out` settles only — no bounce/elastic/spring overshoot
  anywhere (a terminal does not bounce). This differs from generic HyperFrames
  defaults; every frame in this project uses `autoAlpha` + `y` fromTo tweens,
  never `back.out`/`elastic`/scale-pop.
- Terminal text reveals as incremental output (character-by-character typing,
  or line-by-line cascade) — the reveal mechanic IS the content.
- One hairline grid (opacity ~0.18, static) behind every scene for depth.

## Exception: the HTML-export document (Frame 4)

The browser-window CHROME (frame, url bar, traffic dots) follows this
project's dark terminal identity. The DOCUMENT rendered *inside* the browser
keeps the real, captured `demo_board_report.html` styling (`#fafafa` ground,
white card, `#1a1a1a` text) — that page is real tool output, not brand
chrome, so it is never re-skinned to the dark palette.

## Negative list

- No gradient ground, no second accent hue.
- No drop shadow, no rounded corners, no springy/bouncy easing.
- No invented terminal output — mono-font lines are sourced from
  `capture/assets/` (real captured `openexec` command output) wherever
  possible.
