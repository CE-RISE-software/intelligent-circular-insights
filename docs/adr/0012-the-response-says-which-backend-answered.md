# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium

# The response, not the request, says which backend answered

- Status: accepted
- Date: 2026-09-21
- Sprint: 3

## Context

The workbench can be switched between two backends. The switch is a preference
held in the browser and sent as `X-Backend-Mode` on every request.

A preference is not a fact. The backend resolves the mode against what this
deployment actually *built*: an unrecognised value falls back to the default, and
so does a mode whose bundle was never constructed. Both fallbacks are deliberate —
a typo in a header should not be an outage — and both mean the served backend can
differ from the requested one.

Sprint 1 set `X-Backend-Mode-Used` in the Search handler alone. That was enough to
make Search honest and left every other window free to lie, including the 422 path,
where the handler never runs at all and is therefore exactly where a badge is most
likely to go stale.

## Decision

**The response header is the single source of truth about which backend answered,
and it is set by middleware on every response.**

Three consequences, each load-bearing:

1. `ModeMiddleware` resolves the mode once per request, stashes the resolution on
   `request.state`, and stamps `X-Backend-Mode-Used` on the way out. The `get_bundle`
   dependency reads that stash rather than re-resolving, so the handler and the
   header cannot disagree. A test asserts the body's `mode` field equals the header.

2. The header is set for *every* status, including the 422 a mode returns when it
   cannot serve a feature. An honest decline still has to say who declined.

3. The frontend badge renders the header and never the preference. When they differ
   it turns amber and says "fell back", because a silently downgraded backend
   produces answers of a different rigour under an unchanged interface.

Two companion headers carry the rest of the resolution: `X-Backend-Mode-Source`
("header" or "default") and `X-Backend-Mode-Warning`, set only when a requested
mode was refused. All three are in the CORS `expose_headers` list; a browser cannot
read a response header that is not.

## Consequences

The Settings panel offers only modes the backend reports as *built* — `mode_allowed`
comes from the bundle registry, not from configuration — so the UI cannot present a
choice that would immediately fall back. The fallback path still exists and is still
tested, because a stale browser tab can outlive a redeployment.

Cost: every response carries roughly sixty bytes it did not before, and one
middleware frame runs per request. Both are negligible against a badge that can
misreport which backend produced a number a reviewer is reading.
