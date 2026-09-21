#!/usr/bin/env bash
# Install or repair apps/web/node_modules.
#
# node_modules lives OUTSIDE the repository and is symlinked in. Installing it
# here generates thousands of file events in a synced folder, which on this setup
# repeatedly killed the connection to the machine. A symlink is one file.
#
# The target defaults to $HOME/.ici-web-modules. Do not point it at /tmp: the link
# then dangles after a reboot and the next person sees "Cannot find module 'vite'"
# with nothing to suggest the install is fine and only the link is broken.
#
# Safe to re-run. It reinstalls only when the lockfile has moved or the link is
# broken, so `make web-check` can call it without adding a minute to every build.
set -euo pipefail

QUIET=${1:-}
WEB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STORE="${ICI_WEB_MODULES:-$HOME/.ici-web-modules}"

say() { [ "$QUIET" = "--quiet" ] || echo "$@"; }

# A symlink whose target is gone is the case this script exists for: `-e` follows
# the link and is false, while `-L` is true.
if [ -L "$WEB/node_modules" ] && [ ! -e "$WEB/node_modules" ]; then
    say "▸ node_modules points at something that no longer exists — repairing."
    rm -f "$WEB/node_modules"
fi

needs_install=0
[ -d "$STORE/node_modules" ] || needs_install=1
if [ -f "$STORE/package-lock.json" ]; then
    cmp -s "$WEB/package-lock.json" "$STORE/package-lock.json" || needs_install=1
else
    needs_install=1
fi

if [ "$needs_install" -eq 1 ]; then
    say "▸ installing into $STORE"
    mkdir -p "$STORE"
    cp "$WEB/package.json" "$WEB/package-lock.json" "$STORE/"
    ( cd "$STORE" && npm ci --no-audit --no-fund )
else
    say "▸ $STORE is current"
fi

ln -sfn "$STORE/node_modules" "$WEB/node_modules"
say "✓ apps/web/node_modules → $STORE/node_modules"

# Playwright needs a browser. cdn.playwright.dev is refused on some managed
# networks, so ICI_CHROMIUM lets the gate use one already on disk instead of
# being unrunnable there.
if [ -n "${ICI_CHROMIUM:-}" ]; then
    say "▸ Playwright will use ICI_CHROMIUM=$ICI_CHROMIUM"
fi
