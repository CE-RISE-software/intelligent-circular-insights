# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Check a product record against a schema profile, and report typed violations.

The deliverable is never a boolean. Whoever has to repair the record needs to know
which field, which rule, and what was expected — so violations carry a JSON Pointer
or a SHACL focus node.

Thin on purpose, and worth having anyway. This is where record-level policy lands:
the check is stamped into the ledger, so a repair that follows can be read back
against the conformance state it was answering. Until Sprint 3 the router called
``bundle.schemas.conform`` straight through — which worked, and quietly meant no
such policy had anywhere to live.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.ids import CorrelationId, ProfileId
from ici_core.domain.record import ConformanceReport, DPPRecord
from ici_core.domain.trace import TraceStep
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
        report = self.bundle.schemas.conform(record, profile)
        self.bundle.ledger.record(
            correlation_id,
            TraceStep(
                "validate",
                f"{record.dpp_id} against {profile}: "
                + ("conforms" if report.conforms else f"{len(report.violations)} violations"),
            ),
        )
        return report


__all__ = ["ValidateRecord"]
