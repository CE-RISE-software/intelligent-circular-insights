# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""An in-process provenance ledger.

Lives in the core because it holds no I/O: it collects trace steps for a request
and hands back the finished trace. A durable ledger would be an adapter; this one
is a dictionary, which is what a single process needs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ici_core.domain.ids import CorrelationId
from ici_core.domain.modes import DEFAULT_MODE, BackendMode
from ici_core.domain.trace import Trace, TraceStep


@dataclass
class InMemoryLedger:
    """Implements ``ProvenanceLedger``."""

    mode: BackendMode = DEFAULT_MODE
    steps: dict[CorrelationId, list[TraceStep]] = field(default_factory=dict)

    def record(self, cid: CorrelationId, step: TraceStep) -> None:
        self.steps.setdefault(cid, []).append(step)

    def trace(self, cid: CorrelationId) -> Trace:
        return Trace(correlation_id=cid, mode=self.mode, steps=tuple(self.steps.get(cid, [])))
