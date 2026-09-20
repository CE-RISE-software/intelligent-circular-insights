# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""An in-memory product-record repository.

Normal mode keeps records in memory: the workbench's Validate and Synthesize
windows hand a record in and get one back, and nothing yet needs them to outlive
a process. The port exists so that swapping in a real store later is a bundle
change, not a rewrite.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from ici_core.domain.ids import DppId
from ici_core.domain.record import DPPRecord


@dataclass
class InMemoryRepository:
    """Implements ``DPPRepository``."""

    records: dict[DppId, DPPRecord] = field(default_factory=dict)

    def get(self, dpp_id: DppId) -> DPPRecord | None:
        return self.records.get(dpp_id)

    def put(self, record: DPPRecord) -> None:
        self.records[record.dpp_id] = record

    def list_ids(self) -> Sequence[DppId]:
        return sorted(self.records)
