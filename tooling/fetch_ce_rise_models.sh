#!/usr/bin/env bash
# Vendor the 17 CE-RISE data models into schemas/ce-rise/.
#
# Run this on a machine with access to codeberg.org.
#
#   ./tooling/fetch_ce_rise_models.sh            # clone or update all 17
#   ./tooling/fetch_ce_rise_models.sh --check    # report drift, change nothing
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/schemas/ce-rise"
BASE="https://codeberg.org/CE-RISE-models"
CHECK_ONLY="${1:-}"

MODELS=(
  dp-architecture
  dp-record-metadata
  dp-record-custody
  dp-access-and-governance
  product-profile
  material-profile
  usage-and-maintenance
  integrated-lca
  circularity-and-eol
  re-indicators-specification
  compliance-and-standards
  data-quality-framework
  uncertainty-quantification
  metrological-traceability
  diagnostic-results
  traceability-and-life-cycle-events
  template-data-model
)

mkdir -p "$DEST"
MANIFEST="$DEST/VENDOR.md"
TMP="$(mktemp)"

{
  echo "# Vendored CE-RISE data models"
  echo
  echo "Source: <$BASE>  ·  Fetched: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Regenerate with \`./tooling/fetch_ce_rise_models.sh\`."
  echo
  echo "| Model | Commit | Files |"
  echo "|---|---|---|"
} > "$TMP"

for m in "${MODELS[@]}"; do
  target="$DEST/$m"
  if [ -d "$target/.git" ]; then
    if [ "$CHECK_ONLY" = "--check" ]; then
      git -C "$target" fetch --quiet origin || { echo "!! unreachable: $m"; continue; }
      local_sha="$(git -C "$target" rev-parse HEAD)"
      remote_sha="$(git -C "$target" rev-parse '@{u}' 2>/dev/null || echo "$local_sha")"
      [ "$local_sha" != "$remote_sha" ] && echo "DRIFT  $m  $local_sha -> $remote_sha"
    else
      echo ">> updating $m"
      git -C "$target" pull --quiet --ff-only
    fi
  else
    [ "$CHECK_ONLY" = "--check" ] && { echo "MISSING  $m"; continue; }
    echo ">> cloning $m"
    git clone --quiet --depth 1 "$BASE/$m.git" "$target"
  fi

  if [ -d "$target/.git" ]; then
    sha="$(git -C "$target" rev-parse --short HEAD)"
    n="$(find "$target" -type f -not -path '*/.git/*' | wc -l | tr -d ' ')"
    echo "| [\`$m\`]($BASE/$m) | \`$sha\` | $n |" >> "$TMP"
  fi
done

if [ "$CHECK_ONLY" != "--check" ]; then
  mv "$TMP" "$MANIFEST"
  echo
  echo "Vendored into $DEST"
  echo "Manifest: $MANIFEST"
  echo "Commit this directory — the application never fetches schemas at runtime."
else
  rm -f "$TMP"
fi
