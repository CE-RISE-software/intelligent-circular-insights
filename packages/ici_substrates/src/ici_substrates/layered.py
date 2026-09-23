# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Two impact engines behind one port, routed by which one owns the subject.

CE-RISE mode is meant to *do the same features* over CE-RISE data, not merely to
unlock an extra window. For Carbon that means the WP3 graph must actually answer
when the subject is one it models.

What it does **not** mean is substituting one engine for the other. The graph solves
`BatteryPackPEFStudy` — a foreground inventory over a documented proxy factor pack,
declared per kilowatt-hour — and reports 0.059384 kg CO₂ eq. The factor table reports
21,362 kg CO₂e for `generic_bev_pack_60kwh` over a whole product lifecycle. Those are
different systems with different boundaries and different functional units, four
orders of magnitude apart. Mapping one onto the other to make the mode switch "do
something" would produce a confidently wrong number, which is worse than doing
nothing.

So this routes rather than replaces. Each engine keeps the subjects it actually
models; CE-RISE mode simply has more of them, and every result names the engine that
produced it. A caller can therefore tell a graph-solved figure from a table-multiplied
one without reading the docs, which is the distinction the whole two-backend design
exists to make visible.

The ordering of ``subjects()`` puts the graph first because in CE-RISE mode that is
the subject the mode exists to offer, and a picker should lead with it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from ici_core.domain.errors import CapabilityError
from ici_core.domain.impact import (
    ImpactRequest,
    ImpactResult,
    Provenance,
    SubjectRef,
)
from ici_core.ports import ImpactEngine

ENGINE_GRAPH = "pefdpp-graph"
ENGINE_FACTORS = "csv-factors"


@dataclass
class LayeredImpactEngine:
    """Implements ``ImpactEngine`` by delegating to whichever engine owns the subject.

    ``preferred`` is consulted first and answers only for subjects it declares.
    ``fallback`` answers for everything else, which is what keeps the products the
    graph has never heard of working exactly as they did before the mode existed.
    """

    preferred: ImpactEngine
    fallback: ImpactEngine
    preferred_name: str = ENGINE_GRAPH
    fallback_name: str = ENGINE_FACTORS
    _owned: frozenset[str] = field(default=frozenset(), init=False, repr=False)

    def __post_init__(self) -> None:
        # Resolved once. Asking the graph on every request would re-walk it for a
        # membership test, and the mounted set does not change at runtime.
        object.__setattr__(self, "_owned", frozenset(s.id for s in self.preferred.subjects()))

    # -- ImpactEngine -------------------------------------------------------
    def subjects(self) -> Sequence[SubjectRef]:
        return (*self.preferred.subjects(), *self.fallback.subjects())

    def engine_for(self, subject: SubjectRef) -> str:
        """Which engine will answer. Public so a router can report it without assessing."""
        return self.preferred_name if subject.id in self._owned else self.fallback_name

    def assess(self, subject: SubjectRef, req: ImpactRequest) -> ImpactResult:
        graph_owns = subject.id in self._owned
        engine = self.preferred if graph_owns else self.fallback
        name = self.preferred_name if graph_owns else self.fallback_name
        result = engine.assess(subject, req)
        # Prepended, so a reader sees which engine answered before the engine's own
        # caveats rather than after them.
        return _with_diagnostic(result, f"engine: {name}")

    def explain(self, result: ImpactResult, target: str) -> Provenance:
        """Explained by the engine that produced it, never the other one.

        A derivation from a different engine would be a second, independent account
        that happens to concern the same subject — not an explanation of this result.
        """
        owner = self.preferred if result.subject.id in self._owned else self.fallback
        return owner.explain(result, target)


def _with_diagnostic(result: ImpactResult, note: str) -> ImpactResult:
    from dataclasses import replace

    return replace(result, diagnostics=(note, *result.diagnostics))


@dataclass
class ModeAwareImpactEngine:
    """The single-engine case, so Normal mode reports its engine too.

    Without this the diagnostic would appear only in CE-RISE mode, and a reader
    comparing the two could reasonably conclude that Normal mode's engine was
    unnamed rather than simply the only one available.
    """

    engine: ImpactEngine
    name: str = ENGINE_FACTORS

    def subjects(self) -> Sequence[SubjectRef]:
        return self.engine.subjects()

    def engine_for(self, subject: SubjectRef) -> str:
        return self.name

    def assess(self, subject: SubjectRef, req: ImpactRequest) -> ImpactResult:
        return _with_diagnostic(self.engine.assess(subject, req), f"engine: {self.name}")

    def explain(self, result: ImpactResult, target: str) -> Provenance:
        return self.engine.explain(result, target)


__all__ = [
    "ENGINE_FACTORS",
    "ENGINE_GRAPH",
    "CapabilityError",
    "LayeredImpactEngine",
    "ModeAwareImpactEngine",
]
