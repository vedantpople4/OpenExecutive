---
workflow: general-video
flow: companion
storyboard: no
message: "openexec run turns a business decision into a real, structured board debate in one command"
destination: readme-embed
aspect: 1920x1080
language: en
length: 75s
angle: literal-demo
---

## Intent

A demo/walkthrough video for OpenExec (CLI tool simulating a CEO/CFO/CTO/CMO
board debate on a business decision). Unlike the project's existing abstract,
typographic promo (`videos/openexec-promo`), this video is a literal,
developer-facing product demo: real config, the real terminal, the real
`openexec run` command, real streamed agent "thinking," and the real
generated `board_report.md`. Tone: confident, technical, unglamorous —
show the actual tool doing the actual work. Completely independent identity
from any other video in this repo (see `frame.md`) — no shared palette,
fonts, or story shape.

## Assets

- config/openexec.yaml — real project config, shown as a config beat.
- settings.json — real AI-provider config (LM Studio endpoint/model), shown as config beat.
- `openexec config show` real captured output — real resolved config JSON.
- Real captured `openexec run "Should we launch a free tier to drive user growth, or stay paid-only to protect margins?" --verbose` session (stdout log) — the terminal / "thinking" scene's source content, captured live in this session, not invented.
- Real generated `board_report.md` from that same run — the final report beat.

## Customizations

- None from the capability menu opted into yet — plain terminal-capture demo, condensed to 60-90s per user's explicit choice.

## Notes

- User explicitly required: "this is a completely new video, don't refer anything from the past" — no reuse of `videos/openexec-promo`'s palette (ink/cream/fire-orange), fonts (Barlow), story shape, or assets.
- No stylized/recreated terminal content — every mono-font line in the composition must trace to a real captured file or real command output from this session.
- User has no live screen-recording tool available; real content was obtained by actually running the CLI (LM Studio backend) and capturing its stdout + output file, per user's explicit choice on how to source the footage.
