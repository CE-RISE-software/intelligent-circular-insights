# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Expand one number or claim into its full derivation.

The audit panel calls this when a practitioner clicks a figure: which sources,
which factors, which scaling chain, which arithmetic. In CE-RISE mode it reaches
all the way to the triple and the file it lives in.

Sprint 1 fills the body.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.envelope import ReliabilityEnvelope
from ici_core.domain.impact import Provenance
from ici_core.usecases.deps import ProviderBundle


@dataclass(frozen=True)
class ExplainAnswer:
    bundle: ProviderBundle

    def __call__(self, envelope: ReliabilityEnvelope, target: str) -> Provenance:
        raise NotImplementedError("Sprint 1")
