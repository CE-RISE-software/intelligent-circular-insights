# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""An in-memory product-record repository.

Normal mode keeps records in memory: the workbench's Validate and Synthesize
windows hand a record in and get one back, and nothing yet needs them to outlive
a process. The port exists so that swapping in a real store later is a bundle
change, not a rewrite.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ici_core.domain.ids import DppId
from ici_core.domain.record import DPPRecord


@dataclass
class InMemoryRepository:
    """Implements ``DPPRepository``."""

    records: dict[DppId, DPPRecord] = field(default_factory=dict)

    @classmethod
    def from_directory(cls, directory: Path) -> InMemoryRepository:
        """Load complete, operator-provisioned reference records without rewriting them."""
        records: dict[DppId, DPPRecord] = {}
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("dpp_id"), str):
                raise ValueError(f"reference record {path.name} requires a string dpp_id")
            identity = DppId(payload["dpp_id"])
            if not identity or identity in records:
                raise ValueError("reference records require unique, nonempty dpp_id values")
            # Reject non-JSON/non-finite input at startup, before it can reach a prompt.
            json.dumps(payload, allow_nan=False)
            records[identity] = DPPRecord(dpp_id=identity, payload=payload)
        return cls(records)

    def get(self, dpp_id: DppId) -> DPPRecord | None:
        return self.records.get(dpp_id)

    def put(self, record: DPPRecord) -> None:
        self.records[record.dpp_id] = record

    def list_ids(self) -> Sequence[DppId]:
        return sorted(self.records)
