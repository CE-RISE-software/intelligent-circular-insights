# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Calibrators: turning a raw score into something that behaves like a probability.

Isotonic ships as the default because it is what the published system does.
Temperature and a vector calibrator are here, unfitted, because the seat is the
point (ADR 0007): the in-domain ECE problem is plausibly caused by collapsing the
signal vector to a scalar *before* a monotone map is applied, and a monotone map
cannot recover what the collapse discarded. Testing that is a separate exercise;
making it testable without a refactor costs this file.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from ici_core.domain.confidence import CalibrationDiagnostics, SignalVector
from ici_core.domain.ids import CalibratorId


@dataclass
class IdentityCalibrator:
    """Clamps to [0,1] and nothing else. The honest default before any fitting."""

    @property
    def id(self) -> CalibratorId:
        return CalibratorId("identity")

    def fit(self, signals: Sequence[SignalVector], correct: Sequence[bool]) -> None:
        return None

    def calibrate(self, signals: SignalVector, raw: float) -> float:
        return max(0.0, min(1.0, raw))

    def diagnostics(self) -> CalibrationDiagnostics:
        return CalibrationDiagnostics()


@dataclass
class IsotonicCalibrator:
    """Pool-adjacent-violators isotonic regression — the published choice.

    Monotone by construction, so it can reorder nothing: an answer the raw score
    ranked higher never comes out calibrated lower.
    """

    _x: list[float] = field(default_factory=list, init=False)
    _y: list[float] = field(default_factory=list, init=False)
    _fitted: bool = field(default=False, init=False)
    _diag: CalibrationDiagnostics = field(default_factory=CalibrationDiagnostics, init=False)

    @property
    def id(self) -> CalibratorId:
        return CalibratorId("isotonic" if self._fitted else "isotonic-unfitted")

    def fit(self, signals: Sequence[SignalVector], correct: Sequence[bool]) -> None:
        raws = [_mean(tuple(s.values.values())) for s in signals]
        truths = [1.0 if c else 0.0 for c in correct]
        pairs = sorted(zip(raws, truths, strict=False))
        if not pairs:
            return
        xs = [p[0] for p in pairs]
        ys = _pav([p[1] for p in pairs])
        self._x, self._y, self._fitted = xs, ys, True
        self._diag = CalibrationDiagnostics(
            ece=_ece(xs, [p[1] for p in pairs]),
            brier=sum((a - b) ** 2 for a, b in zip(ys, (p[1] for p in pairs), strict=False))
            / len(ys),
            n_samples=len(ys),
        )

    def calibrate(self, signals: SignalVector, raw: float) -> float:
        if not self._fitted:
            return max(0.0, min(1.0, raw))
        if raw <= self._x[0]:
            return self._y[0]
        if raw >= self._x[-1]:
            return self._y[-1]
        for i in range(1, len(self._x)):
            if raw <= self._x[i]:
                span = self._x[i] - self._x[i - 1]
                if span == 0:
                    return self._y[i]
                t = (raw - self._x[i - 1]) / span
                return self._y[i - 1] + t * (self._y[i] - self._y[i - 1])
        return self._y[-1]

    def diagnostics(self) -> CalibrationDiagnostics:
        return self._diag


@dataclass
class TemperatureCalibrator:
    """A single-parameter logistic squash. Present, unfitted — see the module note."""

    temperature: float = 1.0

    @property
    def id(self) -> CalibratorId:
        return CalibratorId(f"temperature-{self.temperature:g}")

    def fit(self, signals: Sequence[SignalVector], correct: Sequence[bool]) -> None:
        return None

    def calibrate(self, signals: SignalVector, raw: float) -> float:
        t = self.temperature or 1.0
        return 1.0 / (1.0 + math.exp(-(raw - 0.5) * 4.0 / t))

    def diagnostics(self) -> CalibrationDiagnostics:
        return CalibrationDiagnostics()


def _pav(ys: list[float]) -> list[float]:
    """Pool adjacent violators: the smallest monotone fit to the data."""
    values = [[y, 1.0] for y in ys]
    i = 0
    while i < len(values) - 1:
        if values[i][0] > values[i + 1][0]:
            total = values[i][0] * values[i][1] + values[i + 1][0] * values[i + 1][1]
            weight = values[i][1] + values[i + 1][1]
            values[i] = [total / weight, weight]
            del values[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    out: list[float] = []
    for value, weight in values:
        out.extend([value] * int(weight))
    return out


def _mean(values: tuple[float, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


def _ece(confidences: Sequence[float], correct: Sequence[float], bins: int = 10) -> float:
    """Expected calibration error: the weighted gap between confidence and accuracy."""
    if not confidences:
        return 0.0
    total = 0.0
    n = len(confidences)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        members = [
            (c, y)
            for c, y in zip(confidences, correct, strict=False)
            if (lo < c <= hi) or (b == 0 and c == 0)
        ]
        if not members:
            continue
        avg_conf = sum(c for c, _ in members) / len(members)
        accuracy = sum(y for _, y in members) / len(members)
        total += (len(members) / n) * abs(avg_conf - accuracy)
    return total
