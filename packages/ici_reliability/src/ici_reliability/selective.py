# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The answer-or-abstain decision.

Separate from the calibrator on purpose. The threshold is a deployment policy — a
mandated coverage floor in one setting, stricter abstention in another — and the
paper's position is that operating points are policy choices. A policy choice
lives in a request, not in a constant, and comes back in the response so an
auditor can see which one produced a given answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.confidence import Confidence, OperatingPoint
from ici_core.domain.envelope import Decision


@dataclass
class ThresholdSelectivePolicy:
    """Implements ``SelectivePolicy``."""

    def threshold_for(self, coverage_target: float) -> float:
        """A threshold for a desired coverage, absent a fitted risk-coverage curve.

        Deliberately crude and deliberately obvious: with no held-out data to fit
        against, the honest move is a linear stand-in rather than a number that
        looks principled. Fitting this from a real curve is `ici_eval`'s job.
        """
        return max(0.0, min(1.0, 1.0 - coverage_target))

    def decide(self, confidence: Confidence, point: OperatingPoint) -> Decision:
        return Decision.ANSWER if point.admits(confidence) else Decision.ABSTAIN
