# OpenExec — landing page

Static marketing site: `index.html` + `styles.css` + `script.js`, no build
step, no dependencies, no framework. It lives in this repo but deploys as its
**own** Vercel project, separate from `frontend/` (the actual Vite/React app)
and `backend/`. Nothing here imports from or builds against either.

## Local preview

```
cd landing
python3 -m http.server 8934
```

Open http://localhost:8934. Every CTA links to `/app.html` directly (not the
extensionless `/app`), specifically so this zero-setup server works without
any caveats — no clean-URL rewriting needed locally.

For the most production-accurate preview — real `vercel.json` header/redirect
behavior, `/app.html` canonicalizing to `/app` the way `cleanUrls` does in
prod — use `npx vercel dev` instead. Not required for day-to-day editing.

## Deploy to Vercel — first time (dashboard)

1. https://vercel.com/new → import this GitHub repo.
2. When it asks for **Root Directory**, set it to `landing`. This is the one
   setting that matters — it's what scopes the deploy to this folder instead
   of the whole monorepo.
3. **Framework Preset**: "Other". There's no build command — Vercel serves
   the static files as-is.
4. Deploy.

After the first import, every push to the project's production branch (set
in the Vercel project's Git settings — defaults to this repo's default
branch) redeploys automatically. Pushes to any other branch get their own
preview URL, which is useful for reviewing copy/design changes before they
go live.

## Deploy to Vercel — CLI alternative

```
npx vercel           # first run: links this folder to a Vercel project, deploys a preview
npx vercel --prod    # promotes the current state to production
```

Run these from inside `landing/`, not the repo root — the CLI treats
whatever directory you run it in as the project root.

## Before this goes live

- **`/app` is a placeholder page, not the real app.** Every CTA on the page
  (nav bar, hero, footer's closing CTA band) links to `/app`, which resolves
  to `app.html` — a static "the live app is coming soon" page, not a redirect.
  Once the real app has a URL, either swap the three `/app` links for the
  real address, or turn `/app` back into a `redirects` rule in `vercel.json`
  pointing at it — that keeps it a one-line change instead of three again.
- **There's no pricing section.** There was no real pricing to put there, and
  a made-up number is worse than none. Add one when there's a real offer.

## Files

| File | What it is |
|---|---|
| `index.html` | Full page markup — nav, hero, how-it-works, the board, live showcase, CTA band, footer |
| `styles.css` | All styling. Dark-only by design (matches the app, which also has no light mode) |
| `script.js` | Sticky-nav scroll state, mobile-menu close-on-tap, the hero's rotating "X is thinking" indicator |
| `vercel.json` | Redirects + baseline security headers |
