# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Request-local audit, merged explicitly into the immutable core trace."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from ici_core.domain.trace import CostAccount, Trace, TraceStep
from ici_llm.prompts import RenderedPrompt, canonical
from ici_llm.transport import Request, TransportResult

# Standard text rates per million tokens, checked 2026-09-19. Estimates only:
# https://developers.openai.com/api/docs/models/gpt-4o-mini
# https://developers.openai.com/api/docs/models/gpt-5
DEFAULT_PRICES = {
    "gpt-4o-mini": (0.15, 0.075, 0.60),
    "gpt-5": (1.25, 0.125, 10.0),
    "text-embedding-3-small": (0.02, 0.02, 0.0),
}


@dataclass
class AuditLog:
    prices: dict[str, tuple[float, float, float]] = field(
        default_factory=lambda: dict(DEFAULT_PRICES)
    )
    steps: list[TraceStep] = field(default_factory=list)
    hashes: list[str] = field(default_factory=list)
    cost: CostAccount = field(default_factory=CostAccount)
    model: str | None = None

    def record(
        self, request: Request, result: TransportResult | None, duration_ms: float, status: str
    ) -> None:
        model = str(request.kwargs["model"])
        usage = (result.response.get("usage") or {}) if result else {}
        prompt = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        completion = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
        input_details = usage.get("prompt_tokens_details", usage.get("input_tokens_details")) or {}
        output_details = (
            usage.get("completion_tokens_details", usage.get("output_tokens_details")) or {}
        )
        cached = min(prompt, int(input_details.get("cached_tokens", 0) or 0))
        reasoning = int(output_details.get("reasoning_tokens", 0) or 0)
        replayed = bool(result and result.replayed)
        offline_failure = status in {"CassetteMiss", "CassetteCorrupt"}
        rates = self.prices.get(model)
        estimated = (
            ((prompt - cached) * rates[0] + cached * rates[1] + completion * rates[2]) / 1_000_000
            if rates
            else None
        )
        # Replay reports historical usage in the event, but spends nothing now.
        billed = 0.0 if replayed or offline_failure else (estimated or 0.0)
        self.cost = self.cost.plus(
            CostAccount(
                prompt_tokens=prompt,
                completion_tokens=completion,
                reasoning_tokens=reasoning,
                llm_calls=0 if replayed or offline_failure else 1,
                usd=billed,
            )
        )
        if request.prompt_hash:
            self.hashes.append(request.prompt_hash)
        if request.endpoint != "embeddings":
            self.model = model
        detail = {
            "model": model,
            "response_model": result.response.get("model") if result else None,
            "prompt_id": request.prompt_id,
            "prompt_hash": request.prompt_hash,
            "request_hash": request.key,
            "replayed": replayed,
            "status": status,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "reasoning_tokens": reasoning,
            "estimated_usd": estimated,
            "usage_available": bool(usage),
        }
        self.steps.append(TraceStep("llm", canonical(detail), duration_ms))

    def guard(self, name: str, passed: bool) -> None:
        self.steps.append(TraceStep("guard", canonical({"name": name, "passed": passed})))

    def prompt(self, prompt: RenderedPrompt) -> None:
        self.hashes.append(prompt.hash)
        self.steps.append(TraceStep("prompt", canonical({"id": prompt.id, "hash": prompt.hash})))

    def enrich(self, trace: Trace) -> Trace:
        return replace(
            trace,
            steps=(*trace.steps, *self.steps),
            cost=trace.cost.plus(self.cost),
            prompt_hashes=(*trace.prompt_hashes, *self.hashes),
            model=self.model or trace.model,
        )
