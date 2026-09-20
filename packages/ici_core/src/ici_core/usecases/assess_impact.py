# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Environmental impact, through whichever engine the mode bound.

Normal mode works from flat product profiles and CSV factor tables: fast, broad,
shallow. CE-RISE mode solves the supply chain off an RDF graph with the Circular
Footprint Formula. This use case does not know the difference, which is the point.

Sprint 1 fills the body.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.envelope import ReliabilityEnvelope
from ici_core.domain.ids import CorrelationId
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.usecases.deps import ProviderBundle


@dataclass(frozen=True)
class AssessImpact:
    bundle: ProviderBundle

    def __call__(
        self,
        subject: SubjectRef,
        req: ImpactRequest,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
        point: OperatingPoint | None = None,
    ) -> ReliabilityEnvelope:
        raise NotImplementedError("Sprint 1")
