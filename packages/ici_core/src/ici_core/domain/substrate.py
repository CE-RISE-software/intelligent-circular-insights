# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Mounted knowledge, and how much of the workload it actually reaches.

``coverage`` is the instrument ADR 0005 exists for: the published symbolic layer
fires on 7.96% of questions with observed precision 1.000, so a new substrate has
to be judged on whether it widens reach without costing precision. The registry
can report that per substrate. Pointing it at a corpus is a separate exercise.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ici_core.domain.ids import SubstrateId


@dataclass(frozen=True)
class Substrate:
    """A mounted source of structured facts."""

    id: SubstrateId
    title: str
    kind: str
    """'ontology' | 'schema-set' | 'graph' | 'tabular'"""
    version: str | None = None
    source: str | None = None
    subjects: tuple[str, ...] = ()
    queryable: bool = False


@dataclass(frozen=True)
class SubstrateCoverage:
    """Fire rate and conditional precision for one substrate."""

    substrate: SubstrateId
    questions_seen: int = 0
    questions_fired: int = 0
    correct_when_fired: int | None = None

    @property
    def fire_rate(self) -> float:
        if self.questions_seen == 0:
            return 0.0
        return self.questions_fired / self.questions_seen

    @property
    def conditional_precision(self) -> float | None:
        """Correctness given that the substrate fired. None when unlabelled."""
        if self.correct_when_fired is None or self.questions_fired == 0:
            return None
        return self.correct_when_fired / self.questions_fired


@dataclass(frozen=True)
class CoverageReport:
    per_substrate: tuple[SubstrateCoverage, ...] = field(default_factory=tuple)
