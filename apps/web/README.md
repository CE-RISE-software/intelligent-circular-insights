# `apps/web` — the workbench

A Vite + React + TypeScript frontend over `apps/api`. Six windows, two backends,
one interface.

```bash
npm install
npm run dev          # http://localhost:5173, proxying /api to :8000
npm run typecheck    # tsc --noEmit, strict
npm run test:smoke   # Playwright; starts both servers itself
```

The API must be reachable at `127.0.0.1:8000` for `dev`. `test:smoke` starts it
itself, with `LLM_CASSETTE_MODE=replay`, so a smoke run makes no network call and
costs nothing.

## The one rule worth knowing

**The badge in the header reports which backend *answered*, never which one was
asked for.**

The requested mode is a browser preference sent as `X-Backend-Mode`. The backend
resolves it against the bundles this deployment actually built, and falls back —
with a warning — when it cannot honour the request. `ModeMiddleware` stamps
`X-Backend-Mode-Used` on every response, including the 422 a mode returns when it
honestly cannot serve a feature. The client reads that header and publishes it; the
badge turns amber when served ≠ requested.

Everything else follows from that. `src/lib/mode.ts` keeps *requested* and *served*
as two separate values on purpose. `src/lib/api.ts` is the only place `fetch` is
called, so no page can forget to read the header.

## A 422 is a value, not an exception

`ApiResult<T>` is a three-way union: `ok`, `declined`, `failed`. A `declined` is a
backend saying what it cannot do and why — "no knowledge graph is mounted in this
mode; switch to ce-rise" — which is a more useful thing to put in front of someone
than a red box. `DeclinedPanel` renders it in amber with a button that performs the
switch.

## Layout

```
src/
  lib/
    mode.ts      requested vs served mode, localStorage, subscribers
    api.ts       the only fetch in the app; typed routes; ApiResult
    types.ts     response shapes, checked against live responses
    useApi.ts    run + refetch on mode change
  components/
    ModeBadge    reads the response header
    AuditPanel   the reliability envelope: signals, τ, grounding, provenance
    Outcome      the ok / declined / failed branch, once
    GlassCard    surfaces, stats, pills
    SettingsModal  backend switch, model, operating point
  pages/
    Search  Carbon  Validate  CeRiseModels  PefStudio  Compare
  theme/tokens.css   the workbench design system, ported unchanged
```

`Compare` asks both backends the same question at once. It passes an explicit mode,
which the client deliberately excludes from the badge: asking a specific backend
must not retitle the session's own.

## Browser storage

`localStorage` holds three preferences — backend, model, τ. Every read and write is
wrapped, and the app renders correctly when storage throws or returns nothing. No
application state lives there.
