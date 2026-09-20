# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Evidence, and the context pack the answerer is bound to.

The context pack is both the grounding mechanism and the audit trail: what the
model saw is exactly what a reviewer can inspect. That equivalence is the point,
so the pack is immutable and its ids are the only currency a claim may cite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ici_core.domain.ids import EvidenceId, SubstrateId


class EvidenceKind(str, Enum):
    PASSAGE = "passage"
    """A span of a retrieved document."""

    FACT = "fact"
    """A validated fact recalled from persistent memory."""

    DERIVED_TRIPLE = "derived_triple"
    """A triple entailed by the symbolic layer, carrying its rule trace."""

    SUBSTRATE_ROW = "substrate_row"
    """A record or triple read from a mounted substrate."""

    CALC_STEP = "calc_step"
    """A step of a deterministic calculation, with its inputs and arithmetic."""


@dataclass(frozen=True)
class Evidence:
    """One sanctioned piece of support, with a resolvable reference.

    ``ref`` is what a reader follows to check the claim: a passage id, a fact id,
    an IRI, a file-and-line. An Evidence whose ref resolves to nothing is useless
    for audit, so adapters must supply one.
    """

    id: EvidenceId
    kind: EvidenceKind
    text: str
    ref: str
    score: float | None = None
    substrate: SubstrateId | None = None
    source_file: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ref:
            raise ValueError(f"evidence {self.id!r} has no resolvable ref")


@dataclass(frozen=True)
class ContextPack:
    """The deduplicated evidence set the answerer may compose from.

    Deliberately not a list: membership testing is the hot operation, because the
    grounding verifier asks "is this cited id in the pack?" for every claim.
    """

    items: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        seen = [item.id for item in self.items]
        if len(seen) != len(set(seen)):
            raise ValueError("context pack contains duplicate evidence ids")

    @property
    def ids(self) -> frozenset[EvidenceId]:
        return frozenset(item.id for item in self.items)

    def get(self, evidence_id: EvidenceId) -> Evidence | None:
        for item in self.items:
            if item.id == evidence_id:
                return item
        return None

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)

    def merge(self, other: ContextPack) -> ContextPack:
        """Union by evidence id; the first occurrence wins."""
        by_id: dict[EvidenceId, Evidence] = {}
        for item in (*self.items, *other.items):
            by_id.setdefault(item.id, item)
        return ContextPack(tuple(by_id.values()))
