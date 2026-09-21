#!/usr/bin/env bash
# Finish Sprint 3: install the frontend, typecheck, run the smoke gate, commit.
#
# Run from anywhere:  bash revamp/apps/web/finish-sprint3.sh
#
# node_modules is installed OUTSIDE the synced folder and symlinked in. That is
# not a preference: installing 74 packages directly into a folder your Mac is
# syncing produces thousands of file events and, on this setup, repeatedly killed
# the connection. A symlink is one file. node_modules is gitignored either way, so
# nothing about the repository changes.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB="$REPO/apps/web"
STORE="${ICI_WEB_MODULES:-$HOME/.ici-web-modules}"

echo "▸ repo:   $REPO"
echo "▸ web:    $WEB"
echo "▸ store:  $STORE"

# ---------------------------------------------------------------- 1. install
mkdir -p "$STORE"
cp "$WEB/package.json" "$WEB/package-lock.json" "$STORE/"
( cd "$STORE" && npm ci --no-audit --no-fund )

# Replace whatever is at apps/web/node_modules with a link to the store.
rm -rf "$WEB/node_modules" 2>/dev/null || true
ln -sfn "$STORE/node_modules" "$WEB/node_modules"
echo "✓ node_modules → $STORE/node_modules"

# ---------------------------------------------------------------- 2. typecheck
( cd "$WEB" && npx tsc --noEmit ) && echo "✓ typecheck"

# ---------------------------------------------------------------- 3. build
( cd "$WEB" && npx vite build ) && echo "✓ build"

# ------------------------------------------------------------- 4. smoke gate
# Browser binaries land in ~/.cache/ms-playwright, outside the synced folder.
( cd "$WEB" && npx playwright install --with-deps chromium )

export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venv-ici}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
export LLM_CASSETTE_MODE=replay        # no network call, no spend

( cd "$REPO" && uv run pytest tests/ -q ) && echo "✓ python suite"
( cd "$WEB" && npx playwright test --grep smoke ) && echo "✓ smoke gate"

# ------------------------------------------------------------------ 5. commit
cd "$REPO"
git add -A
git commit -F - <<'MSG'
feat(web): the mode switch, and the reliability envelope made visible

apps/web: six windows over the rewrite's API, with the workbench design system
ported across unchanged. The demo's 4,462-line frontend was not carried over
verbatim — its pages call endpoints this rewrite deliberately does not have, and
re-adding those to satisfy the old client would undo the rewrite.

Three things the frontend now makes impossible to get wrong:

The badge reads the response, never the preference. ModeMiddleware resolves the
mode once per request, stashes it on request.state so the handler and the header
cannot disagree, and stamps X-Backend-Mode-Used on every response — including the
422 a mode returns when it cannot serve a feature, which is precisely where a
badge is most likely to go stale, because the handler never ran. Sprint 1 set the
header in the Search handler alone; every other window was free to lie.

A 422 is a value, not an exception. ApiResult<T> is ok | declined | failed, and a
decline renders as the reason plus a button that performs the switch that would
satisfy it.

The audit panel shows the whole envelope: the named signal vector with the weak
signal highlighted, tau marked on the confidence track, the grounding verdict with
claims resolved of total, provenance, and the inference trace.

Also fixes the Sprint 2 bug in a second slot. CE-RISE mode assigned the graph into
the single `substrates` slot, and the CE-RISE Models window went from eighteen
models to none the moment you switched to the more rigorous backend — knowledge
present in the fast mode and absent from the careful one. CompositeSubstrateRegistry
composes instead of replacing, and the invariant is now asserted directly rather
than per feature: a mode that removes knowledge fails the suite.

ImpactEngine gains subjects(), so the Carbon picker is read off the profile
directory rather than hard-coded — which is how the demo's product list drifted
from the data it claimed to describe.

ADR 0012 (the response says which backend answered) and ADR 0013 (a mode adds
substrates; it never exchanges them, refining 0002).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VdjeLK212foPEH9VJU8j7H
MSG

echo
echo "✓ Sprint 3 committed"
git log --oneline | head -3
