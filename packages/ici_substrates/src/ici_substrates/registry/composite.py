# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Several substrates behind one registry port.

``ProviderBundle`` has a single ``substrates`` slot, so mounting a second source of
facts means composing rather than swapping. That distinction is not cosmetic: an
earlier build mounted the WP3 graph by replacing the model catalogue, and the
CE-RISE Models window went empty in CE-RISE mode — eighteen data models present in
the fast backend and absent from the rigorous one, which is exactly backwards.

The same mistake in the impact slot was caught in Sprint 2. This is the general fix:
a mode adds knowledge, and the only way to add through a one-slot port is a composite.

Delegation rules, in one place so they are arguable:

* ``mounted`` concatenates, in mount order.
* ``facts_for`` merges every member's triples. A subject known to two substrates
  gets both views, because suppressing one would silently pick a winner.
* ``coverage_report`` concatenates per-substrate rows rather than summing them.
  ADR 0005 measures fire rate *per substrate*; a pooled average would hide the very
  difference the instrument exists to show.
* Capability methods a member defines and the port does not — ``route``, ``query``,
  ``run_question`` — are forwarded to the first member that has one. Members are
  ordered most-specific-first, so the graph answers graph questions and the
  catalogue answers catalogue questions.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ici_core.domain.impact import SubjectRef
from ici_core.domain.rules import FactGraph
from ici_core.domain.substrate import CoverageReport, Substrate

# Forwarded only when a member actually implements it. Listed explicitly rather
# than forwarding anything: a blanket __getattr__ turns a typo into a silent
# AttributeError somewhere far away.
_FORWARDED = (
    "route",
    "by_layer",
    "models",
    "query",
    "run_question",
    "run_all_questions",
    "coverage_summary",
    "questions",
    "graph",
    "lca",
    "impact",
)


@dataclass
class CompositeSubstrateRegistry:
    """Implements ``SubstrateRegistry`` over an ordered list of member registries."""

    members: tuple[Any, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.members:
            raise ValueError("a composite registry with no members is a bug, not a configuration")

    # -- SubstrateRegistry ---------------------------------------------------
    def mounted(self) -> Sequence[Substrate]:
        out: list[Substrate] = []
        for member in self.members:
            out.extend(member.mounted())
        return out

    def facts_for(self, subject: SubjectRef) -> FactGraph:
        triples = tuple(t for member in self.members for t in member.facts_for(subject).triples)
        return FactGraph(triples)

    def coverage_report(self) -> CoverageReport:
        rows = tuple(
            row for member in self.members for row in member.coverage_report().per_substrate
        )
        return CoverageReport(per_substrate=rows)

    # -- capability forwarding -----------------------------------------------
    def __getattr__(self, name: str) -> Any:
        # Only reached for attributes the dataclass does not define.
        if name in _FORWARDED:
            for member in self.__dict__.get("members", ()):
                if hasattr(member, name):
                    return getattr(member, name)
        raise AttributeError(
            f"no mounted substrate provides {name!r}; "
            f"mounted: {[type(m).__name__ for m in self.__dict__.get('members', ())]}"
        )
