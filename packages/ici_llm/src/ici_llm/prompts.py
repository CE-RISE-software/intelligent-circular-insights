# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Versioned file prompts, loaded identically from a checkout and a wheel."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from string import Template
from typing import Any

import yaml

from ici_core.domain.evidence import ContextPack


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


@dataclass(frozen=True)
class RenderedPrompt:
    id: str
    text: str
    hash: str


class PromptRegistry:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory

    def render(self, name: str, **variables: str) -> RenderedPrompt:
        if not name.replace("_", "").isalnum():
            raise ValueError("invalid prompt name")
        if self.directory is not None:
            source = (self.directory / f"{name}.md").read_text(encoding="utf-8")
        else:
            resource = files("ici_llm").joinpath("prompt_data").joinpath(f"{name}.md")
            if resource.is_file():
                source = resource.read_text(encoding="utf-8")
            else:
                source = (Path(__file__).resolve().parents[2] / "prompts" / f"{name}.md").read_text(
                    encoding="utf-8"
                )
        parts = source.split("---", 2)
        if len(parts) != 3 or parts[0].strip():
            raise ValueError("prompt requires YAML front-matter")
        metadata = yaml.safe_load(parts[1])
        required = {"id", "version", "model_families", "purpose", "variables"}
        if not isinstance(metadata, dict) or not required <= metadata.keys():
            raise ValueError("incomplete prompt metadata")
        if set(metadata["variables"]) != set(variables):
            raise ValueError("prompt variables do not match their declaration")
        text = Template(parts[2].strip()).substitute(variables)
        identity = f"{metadata['id']}@{metadata['version']}"
        digest = hashlib.sha256(canonical({"id": identity, "text": text}).encode()).hexdigest()
        return RenderedPrompt(identity, text, digest)


def evidence_json(pack: ContextPack) -> str:
    # Only sanctioned evidence enters the model context; arbitrary metadata stays out.
    return canonical([{"id": str(e.id), "text": e.text, "ref": e.ref} for e in pack.items])
