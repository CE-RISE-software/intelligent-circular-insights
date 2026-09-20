# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The data-trust seat.

Empty in this release. ``DataTrustProvider`` has a null implementation in both
shipped modes, and the envelope carries an optional ``data_trust`` field.

Why build the seat now: the bias-aware work abstains when a recorded value is
*present but systematically biased*, which needs two extra confidence channels and
an answer object that can carry a debiased value with a credible interval. Adding
those later without the seat means reworking every response type and every
consumer of it. With the seat it is additive. The cost today is this file.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CredibleInterval:
    lower: float
    upper: float
    mass: float = 0.9

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise ValueError("credible interval bounds are inverted")

    @property
    def half_width(self) -> float:
        return (self.upper - self.lower) / 2.0


@dataclass(frozen=True)
class DataTrust:
    """A latent-bias posterior summary for one queried attribute."""

    clean_value: float
    interval: CredibleInterval
    target_sensitivity: float
    group_bias: float
    diagnostics: dict[str, float] | None = None
