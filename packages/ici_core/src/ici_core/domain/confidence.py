# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Confidence signals, calibration, and the operating point.

Two decisions are encoded here, both from ARCHITECTURE.md §9.1.

First, signals stay a *named vector* on the way through, rather than being
collapsed to a scalar before anyone can inspect them. That is what lets an
abstention say which signal was weak, and it is what makes a vector calibrator
expressible later without touching a call site.

Second, the threshold travels with the response. The operating point is a policy
choice — a mandated coverage floor in one deployment, stricter abstention in
another — and a policy choice buried in a constant cannot be audited.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ici_core.domain.ids import CalibratorId, SignalName

# The signals the published system aggregates, named so a trace can cite them.
RETRIEVAL_MARGIN = SignalName("retrieval_margin")
SNIPPET_AGREEMENT = SignalName("snippet_agreement")
SYMBOLIC_FIRED = SignalName("symbolic_fired")
GENERATION_PROBABILITY = SignalName("generation_probability")
MEMORY_SUPPORT = SignalName("memory_support")
# Reserved for the data-trust seat (ARCHITECTURE.md §9.5); absent until it lands.
NEG_POSTERIOR_WIDTH = SignalName("neg_posterior_width")
NEG_TARGET_SENSITIVITY = SignalName("neg_target_sensitivity")


@dataclass(frozen=True)
class SignalVector:
    """Named confidence signals, each measuring a different way an answer is weak."""

    values: Mapping[SignalName, float] = field(default_factory=dict)

    def get(self, name: SignalName, default: float = 0.0) -> float:
        return self.values.get(name, default)

    def names(self) -> tuple[SignalName, ...]:
        return tuple(sorted(self.values))

    def weakest(self) -> SignalName | None:
        """The lowest-valued signal — what an abstention should name.

        Returns None on an empty vector rather than inventing a reason.
        """
        if not self.values:
            return None
        return min(self.values, key=lambda k: self.values[k])

    def with_signal(self, name: SignalName, value: float) -> SignalVector:
        merged = dict(self.values)
        merged[name] = value
        return SignalVector(merged)


@dataclass(frozen=True)
class Confidence:
    """A raw score, its calibrated probability, and who calibrated it."""

    signals: SignalVector = field(default_factory=SignalVector)
    raw: float = 0.0
    calibrated: float = 0.0
    calibrator_id: CalibratorId = CalibratorId("identity")

    def __post_init__(self) -> None:
        if not 0.0 <= self.calibrated <= 1.0:
            raise ValueError(f"calibrated confidence out of [0,1]: {self.calibrated}")


@dataclass(frozen=True)
class OperatingPoint:
    """The thresholds in force for a request, reported back with the answer.

    ``lambda_belief`` and ``lambda_record`` are the other two knobs of the tilted
    spine. They are carried but unused in this release; the data-trust seat reads
    them when it lands, and having the field now means that landing is additive
    rather than a schema change.
    """

    tau: float = 0.5
    coverage_target: float | None = None
    lambda_record: float | None = None
    lambda_belief: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.tau <= 1.0:
            raise ValueError(f"tau out of [0,1]: {self.tau}")
        if self.coverage_target is not None and not 0.0 <= self.coverage_target <= 1.0:
            raise ValueError(f"coverage target out of [0,1]: {self.coverage_target}")

    def admits(self, confidence: Confidence) -> bool:
        return confidence.calibrated >= self.tau


@dataclass(frozen=True)
class CalibrationDiagnostics:
    """What a calibrator reports about itself after fitting."""

    ece: float | None = None
    brier: float | None = None
    n_samples: int = 0
    bins: tuple[tuple[float, float, int], ...] = ()
    """(mean confidence, observed accuracy, count) per bin — a reliability diagram."""
