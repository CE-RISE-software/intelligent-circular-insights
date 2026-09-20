# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The CE-RISE data-model catalogue, and the substrate registry over it.

The 17 models were hard-coded as a Python literal in the demo. Here they are data
(``data/ce_rise_models.json``), because a catalogue that can be replaced by a file
can be refreshed from upstream without a code change — and because the vendored
schemas that will sit beside it are CC-BY-NC-4.0 while this code is EUPL-1.2, so
the boundary between them needs to be a file boundary (ADR 0010).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ici_core.domain.ids import SubstrateId
from ici_core.domain.impact import SubjectRef
from ici_core.domain.rules import FactGraph
from ici_core.domain.substrate import CoverageReport, Substrate, SubstrateCoverage
from ici_substrates.paths import DATA_ROOT

CE_RISE_SOURCE = "https://codeberg.org/CE-RISE-models"


@dataclass(frozen=True)
class CeRiseModel:
    """One published CE-RISE data model, as its vendored LinkML schema declares it.

    Derived from `schemas/ce-rise/*/model/model.yaml` by
    `tooling/build_model_catalog.py`, not hand-maintained. The demo's hand-written
    version had drifted: it listed `template-data-model`, which no longer exists,
    and missed `lci-dataset` and `product-system`, which do.
    """

    id: str
    title: str
    layer: str
    summary: str
    url: str
    version: str = ""
    licence: str = ""
    """Normalised to SPDX. The models declare it as a human string or a URL."""
    licence_declared: str = ""
    namespace: str = ""
    declared_name: str = ""
    """The schema's own ``name:``. Five models underscore it where their repository
    hyphenates, so ``id`` follows the repository and this records the difference."""
    classes: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    @property
    def class_count(self) -> int:
        return len(self.classes)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CeRiseModel:
        return cls(
            id=str(raw["id"]),
            title=str(raw["title"]),
            layer=str(raw["layer"]),
            summary=str(raw.get("summary", "")),
            url=str(raw.get("url", "")),
            version=str(raw.get("version", "")),
            licence=str(raw.get("licence", "")),
            licence_declared=str(raw.get("licence_declared", "")),
            namespace=str(raw.get("namespace", "")),
            declared_name=str(raw.get("declared_name", "")),
            classes=tuple(raw.get("classes", ())),
            keywords=tuple(raw.get("keywords", ())),
        )

    def matches(self, question: str) -> int:
        """How many of this model's keywords the question mentions."""
        lowered = question.lower()
        return sum(1 for kw in self.keywords if kw.lower() in lowered)


def load_catalog(path: Path | None = None) -> tuple[CeRiseModel, ...]:
    source = path or (DATA_ROOT / "ce_rise_models.json")
    raw = json.loads(source.read_text())
    return tuple(CeRiseModel.from_dict(item) for item in raw)


@dataclass
class CeRiseModelRegistry:
    """Implements ``SubstrateRegistry`` for Normal mode.

    Normal mode mounts the catalogue as a *descriptive* substrate: it can say which
    model layer a question belongs to, but it holds no instance data, so
    ``facts_for`` is honestly empty. CE-RISE mode adds the graph substrates that do
    carry facts.
    """

    models: tuple[CeRiseModel, ...] = field(default_factory=load_catalog)
    _seen: int = field(default=0, init=False)
    _fired: int = field(default=0, init=False)

    # -- SubstrateRegistry --------------------------------------------------
    def mounted(self) -> Sequence[Substrate]:
        return [
            Substrate(
                id=SubstrateId("ce-rise-models"),
                title="CE-RISE data models",
                kind="schema-set",
                source=CE_RISE_SOURCE,
                subjects=tuple(m.id for m in self.models),
                queryable=False,
            )
        ]

    def facts_for(self, subject: SubjectRef) -> FactGraph:
        """Empty by design: the catalogue describes shapes, not instances.

        Returning invented triples here would let the symbolic layer 'fire' on
        nothing, which would inflate the coverage number the whole registry exists
        to measure honestly.
        """
        self._seen += 1
        return FactGraph()

    def coverage_report(self) -> CoverageReport:
        return CoverageReport(
            per_substrate=(
                SubstrateCoverage(
                    substrate=SubstrateId("ce-rise-models"),
                    questions_seen=self._seen,
                    questions_fired=self._fired,
                ),
            )
        )

    # -- catalogue queries --------------------------------------------------
    def route(self, question: str) -> tuple[CeRiseModel, ...]:
        """Models whose keywords the question touches, best match first."""
        scored = [(m.matches(question), m) for m in self.models]
        hits = sorted(
            ((score, m) for score, m in scored if score > 0),
            key=lambda pair: (-pair[0], pair[1].id),
        )
        if hits:
            self._fired += 1
        return tuple(m for _, m in hits)

    def by_layer(self) -> dict[str, tuple[CeRiseModel, ...]]:
        layers: dict[str, list[CeRiseModel]] = {}
        for model in self.models:
            layers.setdefault(model.layer, []).append(model)
        return {k: tuple(v) for k, v in sorted(layers.items())}
