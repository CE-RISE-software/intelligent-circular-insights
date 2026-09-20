# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The data-trust seat, unoccupied.

Both shipped modes mount this. It answers "nothing to say" rather than inventing a
trust score, and declares itself null so the UI hides the panel instead of showing
an empty one.

The bias-aware work (`bias_aware_qa/`, ~5,000 LoC of latent-bias posterior, clean
value, credible interval and target sensitivity) lands behind this port later. The
envelope already carries `data_trust` and `operating_point`, so that landing is
additive rather than a schema change — which is the entire reason this file exists
now rather than then.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.datatrust import DataTrust
from ici_core.domain.impact import SubjectRef


@dataclass
class NullDataTrustProvider:
    """Implements ``DataTrustProvider`` with no opinion."""

    def assess(
        self, subject: SubjectRef, attribute: str, point: OperatingPoint
    ) -> DataTrust | None:
        return None

    @property
    def is_null(self) -> bool:
        return True
