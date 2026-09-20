# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Generate a schema-valid product record from a few supplied facts.

Validated against the target schema before it is returned. A schema failure is one
retry with the violation in the prompt, then an error — never a silent pass, since
a plausible-looking invalid passport is worse than no passport.

Sprint 1 fills the body.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ici_core.domain.ids import CorrelationId, ProfileId
from ici_core.domain.record import DPPRecord
from ici_core.usecases.deps import ProviderBundle


@dataclass(frozen=True)
class SynthesizeRecord:
    bundle: ProviderBundle

    def __call__(
        self,
        seed: Mapping[str, Any],
        profile: ProfileId,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
    ) -> DPPRecord:
        raise NotImplementedError("Sprint 1")
