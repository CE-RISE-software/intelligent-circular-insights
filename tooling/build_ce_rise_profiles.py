# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Generate JSON Schemas from the vendored CE-RISE LinkML models.

Run by hand, output committed:

    uv run python -m tooling.build_ce_rise_profiles

Why generate at tooling time rather than at runtime. The models import each other
over `codeberg.org` URLs, and LinkML is a heavy dependency that the service does not
otherwise need. Generating here and committing the result means the API depends on
nothing but `json`, the build is a reviewable diff when a model changes, and a
deployment behind a restricted network — which is the normal case for this project —
can still validate against the real models.

Imports are rewritten to the vendored copy beside each model, so this runs offline.
That is not a convenience: `codeberg.org` is refused by the egress policy on the
machines this is developed on, and a generator that only works with network access
would be a generator nobody runs.

The models' own licence is CC-BY-NC-4.0 and travels with the output; see
`schemas/ce-rise/NOTICE.md`. The generated schemas are a derived form of those
models, not of this repository's EUPL code, which is why they live beside them
rather than under `schemas/`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "schemas" / "ce-rise"
OUT = VENDORED / "_generated"

# `    - https://codeberg.org/CE-RISE-models/<name>/raw/tag/<tag>/generated/schema`
REMOTE_IMPORT = re.compile(r"^(\s*)- https://codeberg\.org/CE-RISE-models/([a-z0-9\-]+)/\S+$", re.M)


def _models() -> dict[str, Path]:
    return {p.parent.parent.name: p for p in sorted(VENDORED.glob("*/model/model.yaml"))}


def _localise(text: str, known: set[str]) -> str:
    """Point every remote CE-RISE import at the copy vendored beside it."""

    def replace(match: re.Match[str]) -> str:
        indent, name = match.group(1), match.group(2)
        return f"{indent}- {name}" if name in known else match.group(0)

    return REMOTE_IMPORT.sub(replace, text)


def _stage(workdir: Path, models: dict[str, Path]) -> Path:
    """Copy the vendored tree as-is, rewriting only the cross-model imports.

    Flattening the models into one directory does not work. Several import their own
    sub-files by relative path — `re-indicators-specification` pulls in a dozen
    `./indicators/*.yaml` — and LinkML resolves those against the importing file's
    own directory. Keeping the layout satisfies both kinds of import at once: the
    relative ones because the neighbours are still where the file expects them, and
    the cross-model ones because they are rewritten to a relative path through the
    preserved tree.
    """
    root = workdir / "ce-rise"
    shutil.copytree(VENDORED, root, dirs_exist_ok=True, ignore=shutil.ignore_patterns("_generated"))
    known = set(models)
    for yaml in root.rglob("*.yaml"):
        text = yaml.read_text(encoding="utf-8")

        def replace(match: re.Match[str], here: Path = yaml) -> str:
            indent, name = match.group(1), match.group(2)
            if name not in known:
                return match.group(0)
            target = root / name / "model" / "model"
            relative = Path(os.path.relpath(target, here.parent)).as_posix()
            return f"{indent}- {relative}"

        rewritten = REMOTE_IMPORT.sub(replace, text)
        if rewritten != text:
            yaml.write_text(rewritten, encoding="utf-8")
    return root


def build() -> int:
    try:
        from linkml.generators.jsonschemagen import JsonSchemaGenerator
    except ImportError:
        print(
            "linkml is not installed. It is a tooling-only dependency:\n"
            "    uv run --with linkml python -m tooling.build_ce_rise_profiles",
            file=sys.stderr,
        )
        return 2

    models = _models()
    if not models:
        print(f"no vendored models under {VENDORED}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[tuple[str, int]] = []
    failed: list[tuple[str, str]] = []

    with tempfile.TemporaryDirectory() as raw:
        root = _stage(Path(raw), models)
        for name in models:
            try:
                schema: dict[str, Any] = json.loads(
                    JsonSchemaGenerator(
                        str(root / name / "model" / "model.yaml"), not_closed=True
                    ).serialize()
                )
            except Exception as exc:
                failed.append((name, f"{type(exc).__name__}: {exc}"[:110]))
                continue
            # Recorded in the artefact so a reader knows what produced it and under
            # what terms, without having to find this script.
            schema["$comment"] = (
                f"Generated from schemas/ce-rise/{name}/model/model.yaml by "
                f"tooling/build_ce_rise_profiles.py. Do not edit. "
                f"The CE-RISE data models are CC-BY-NC-4.0; see ../NOTICE.md."
            )
            (OUT / f"{name}.json").write_text(
                json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            generated.append((name, len(schema.get("$defs", {}))))

    for name, defs in generated:
        print(f"  {name:38} {defs:4} definitions")
    for name, error in failed:
        print(f"  FAILED {name:32} {error}", file=sys.stderr)
    print(f"\n{len(generated)} of {len(models)} models generated into {OUT.relative_to(ROOT)}")
    # A partial run is still useful, so this does not fail the build; the registry
    # offers whatever is present and the count is asserted by a test.
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
