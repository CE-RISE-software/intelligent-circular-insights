# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Symbolic entailment results.

The symbolic layer's value is that its conclusions come with a trace: which rule
fired, on which triples. An entailment nobody can explain is not worth the
precision it claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object: str

    def __str__(self) -> str:
        return f"({self.subject}, {self.predicate}, {self.object})"


@dataclass(frozen=True)
class RuleTrace:
    """Which rule produced a triple, and from what."""

    rule_id: str
    premises: tuple[Triple, ...]
    conclusion: Triple


@dataclass(frozen=True)
class FactGraph:
    """The triples known about a subject, from every mounted substrate."""

    triples: tuple[Triple, ...] = ()

    def __len__(self) -> int:
        return len(self.triples)

    def __bool__(self) -> bool:
        return bool(self.triples)

    def merge(self, other: FactGraph) -> FactGraph:
        seen = {*self.triples, *other.triples}
        return FactGraph(tuple(sorted(seen, key=str)))


@dataclass(frozen=True)
class EntailmentResult:
    """What forward chaining added, and how."""

    derived: tuple[Triple, ...] = ()
    traces: tuple[RuleTrace, ...] = ()
    rules_fired: tuple[str, ...] = ()

    @property
    def fired(self) -> bool:
        """Whether any rule fired.

        This is a confidence signal in its own right: the paper reports symbolic
        precision conditional on firing, so 'did it fire' must be observable.
        """
        return bool(self.rules_fired)


@dataclass(frozen=True)
class ValidationReport:
    """Whether claims survive checking against the rules."""

    checked: int = 0
    violations: tuple[str, ...] = ()
    traces: tuple[RuleTrace, ...] = field(default_factory=tuple)

    @property
    def clean(self) -> bool:
        return not self.violations
