# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Serialize the request's record workflow and LLM audit without shared trace state."""

from dataclasses import asdict
from typing import Any

from fastapi import Response

from ici_core.domain.ids import CorrelationId
from ici_core.usecases.deps import ProviderBundle
from ici_llm.runtime import LLMRequest


def record_trace(
    bundle: ProviderBundle, correlation_id: CorrelationId, llm: LLMRequest, response: Response
) -> dict[str, Any]:
    trace = llm.audit.enrich(bundle.ledger.trace(correlation_id))
    if trace.model:
        response.headers["X-Model-Used"] = trace.model
    return {
        "correlation_id": str(trace.correlation_id),
        "model": trace.model,
        "prompt_hashes": list(trace.prompt_hashes),
        "cost": asdict(trace.cost),
        "steps": [
            {"name": s.name, "detail": s.detail, "duration_ms": s.duration_ms} for s in trace.steps
        ],
    }
