# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The audit trail for one request.

Every step that touched a response lands here: which action the policy chose,
which adapter ran, which guard fired, which prompt was used. The audit panel the
consortium sees is a rendering of this, so it is a first-class output rather than
logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ici_core.domain.ids import CorrelationId
from ici_core.domain.modes import BackendMode


@dataclass(frozen=True)
class CostAccount:
    """What a request consumed. A runaway loop is a bill, so this is measured."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    llm_calls: int = 0
    usd: float = 0.0

    def plus(self, other: CostAccount) -> CostAccount:
        return CostAccount(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            llm_calls=self.llm_calls + other.llm_calls,
            usd=self.usd + other.usd,
        )


@dataclass(frozen=True)
class TraceStep:
    """One thing that happened, named well enough to explain the outcome."""

    name: str
    detail: str = ""
    duration_ms: float | None = None
    at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class Trace:
    """The ordered record of a request."""

    correlation_id: CorrelationId
    mode: BackendMode
    steps: tuple[TraceStep, ...] = ()
    cost: CostAccount = field(default_factory=CostAccount)
    prompt_hashes: tuple[str, ...] = ()
    model: str | None = None

    def with_step(self, step: TraceStep) -> Trace:
        return Trace(
            correlation_id=self.correlation_id,
            mode=self.mode,
            steps=(*self.steps, step),
            cost=self.cost,
            prompt_hashes=self.prompt_hashes,
            model=self.model,
        )

    def step_names(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.steps)
