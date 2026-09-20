# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Check a product record against a schema profile, and report typed violations.

The deliverable is never a boolean. Whoever has to repair the record needs to know
which field, which rule, and what was expected — so violations carry a JSON
Pointer or a SHACL focus node.

Sprint 1 fills the body.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.ids import CorrelationId, ProfileId
from ici_core.domain.record import ConformanceReport, DPPRecord
from ici_core.usecases.deps import ProviderBundle


@dataclass(frozen=True)
class ValidateRecord:
    bundle: ProviderBundle

    def __call__(
        self,
        record: DPPRecord,
        profile: ProfileId,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
    ) -> ConformanceReport:
        raise NotImplementedError("Sprint 1")
