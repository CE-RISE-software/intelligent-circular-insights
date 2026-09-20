# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The confidence signal vector.

Each signal measures a different way an answer can be weak: was the evidence
clearly better than the alternatives, did the snippets agree, did a rule fire,
how sure was the generator. The published system aggregates these into a scalar
before calibrating. Here they stay a *named vector* all the way into the response,
for two reasons — an abstention can then say which signal was weak, and a vector
calibrator becomes expressible later without touching this call site (ADR 0007).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ici_core.domain.confidence import (
    GENERATION_PROBABILITY,
    MEMORY_SUPPORT,
    RETRIEVAL_MARGIN,
    SNIPPET_AGREEMENT,
    SYMBOLIC_FIRED,
    SignalVector,
)
from ici_core.domain.evidence import ContextPack, EvidenceKind
from ici_core.domain.ids import SignalName
from ici_core.domain.query import Query
from ici_core.domain.rules import EntailmentResult
from ici_core.text import tokenize

NAMES: tuple[SignalName, ...] = (
    RETRIEVAL_MARGIN,
    SNIPPET_AGREEMENT,
    SYMBOLIC_FIRED,
    MEMORY_SUPPORT,
    GENERATION_PROBABILITY,
)


@dataclass
class EvidenceSignals:
    """Implements ``ConfidenceSignals``."""

    def names(self) -> Sequence[SignalName]:
        return NAMES

    def emit(
        self,
        q: Query,
        pack: ContextPack,
        entailment: EntailmentResult | None,
        generation_probability: float | None = None,
    ) -> SignalVector:
        return SignalVector(
            {
                RETRIEVAL_MARGIN: _margin(pack),
                SNIPPET_AGREEMENT: _agreement(pack),
                SYMBOLIC_FIRED: 1.0 if (entailment and entailment.fired) else 0.0,
                MEMORY_SUPPORT: _memory_support(pack),
                GENERATION_PROBABILITY: (
                    generation_probability if generation_probability is not None else 0.5
                ),
            }
        )


def _margin(pack: ContextPack) -> float:
    """How far the best passage beat the runner-up, normalised to [0,1].

    A thin margin means retrieval could not distinguish the answer from a
    plausible neighbour, which is a different weakness from having no evidence at
    all — and worth reporting separately.
    """
    scores = sorted((e.score for e in pack.items if e.score is not None), reverse=True)
    if not scores:
        return 0.0
    if len(scores) == 1:
        return 1.0 if scores[0] > 0 else 0.0
    best, second = scores[0], scores[1]
    return 0.0 if best <= 0 else max(0.0, min(1.0, (best - second) / best))


def _agreement(pack: ContextPack) -> float:
    """Mean pairwise token overlap between passages.

    Evidence that agrees with itself is stronger than evidence that does not.
    A single item cannot agree or disagree, so it scores neutral rather than
    perfect — claiming certainty from one source is exactly the failure mode here.
    """
    texts = [set(tokenize(e.text)) for e in pack.items if e.text]
    if len(texts) < 2:
        return 0.5 if texts else 0.0
    overlaps: list[float] = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            union = texts[i] | texts[j]
            overlaps.append(len(texts[i] & texts[j]) / len(union) if union else 0.0)
    return sum(overlaps) / len(overlaps)


def _memory_support(pack: ContextPack) -> float:
    """Share of the pack that is validated memory rather than raw document text."""
    if not pack.items:
        return 0.0
    facts = sum(1 for e in pack.items if e.kind is EvidenceKind.FACT)
    return facts / len(pack.items)
