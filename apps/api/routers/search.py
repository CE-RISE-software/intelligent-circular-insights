# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Search & Answer — the reliability path.

The four published stages plus the grounding check, orchestrated by
``AnswerQuestion`` in the core. This router only translates HTTP to domain types
and back, so the same inference path serves both modes.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request, Response
from pydantic import BaseModel, Field, field_validator

from apps.api.deps import get_bundle, get_llm_request
from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.ids import CorrelationId, ProductId
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.usecases.answer_question import AnswerQuestion
from ici_core.usecases.deps import ProviderBundle
from ici_llm.runtime import LLMRequest

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    q: str = Field(min_length=1)
    product: str | None = None
    domain: str | None = None
    session: str | None = "default"
    tau: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    top_k_documents: int = Field(default=4, ge=0, le=100)
    top_k_memory: int = Field(default=3, ge=0, le=100)

    @field_validator("q")
    @classmethod
    def nonblank_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


@router.post("")
def search(
    req: SearchRequest,
    request: Request,
    response: Response,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    llm: Annotated[LLMRequest, Depends(get_llm_request)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    query = Query(
        text=req.q,
        scope=ProductScope(
            product_id=ProductId(req.product) if req.product else None,
            domain=req.domain,
            session=req.session,
        ),
        correlation_id=CorrelationId(x_correlation_id or "anonymous"),
    )
    settings = request.app.state.settings
    envelope = AnswerQuestion(llm.bind(bundle))(
        query,
        budget=RetrievalBudget(
            top_k_documents=req.top_k_documents,
            top_k_memory=req.top_k_memory,
            max_context_chars=settings.max_context_chars,
        ),
        point=OperatingPoint(tau=req.tau if req.tau is not None else settings.default_tau),
    )
    envelope = llm.finish(envelope)
    if envelope.trace.model is not None:
        response.headers["X-Model-Used"] = envelope.trace.model
    # ModeMiddleware stamps X-Backend-Mode-Used on the way out, for every route
    # and every status, so the UI cannot misreport which backend answered.
    return _serialise(envelope)


def _serialise(env: Any) -> dict[str, Any]:
    return {
        "decision": env.decision.value,
        "mode": env.mode.value,
        "answer": env.answer,
        "abstain_reason": env.abstain_reason,
        # An abstention names the signal that was weak, which is what a
        # practitioner actually asks when the system declines.
        "weak_signal": env.weak_signal,
        "confidence": {
            "raw": env.confidence.raw,
            "calibrated": env.confidence.calibrated,
            "calibrator": str(env.confidence.calibrator_id),
            "signals": dict(env.confidence.signals.values),
        },
        "operating_point": {
            "tau": env.operating_point.tau,
            "coverage_target": env.operating_point.coverage_target,
        },
        "grounding": {
            "verdict": env.grounding.verdict.value,
            "claims_total": env.grounding.claims_total,
            "claims_resolved": env.grounding.claims_resolved,
            "unresolved": [asdict(c) for c in env.grounding.unresolved],
        },
        "evidence": [
            {"id": e.id, "kind": e.kind.value, "ref": e.ref, "score": e.score, "text": e.text[:600]}
            for e in env.evidence
        ],
        "provenance": [
            {"kind": p.kind.value, "ref": p.ref, "source_file": p.source_file, "excerpt": p.excerpt}
            for p in env.provenance
        ],
        "trace": {
            "correlation_id": str(env.trace.correlation_id),
            "model": env.trace.model,
            "prompt_hashes": list(env.trace.prompt_hashes),
            "cost": asdict(env.trace.cost),
            "steps": [
                {"name": s.name, "detail": s.detail, "duration_ms": s.duration_ms}
                for s in env.trace.steps
            ],
        },
        "data_trust": None
        if env.data_trust is None
        else {
            "clean_value": env.data_trust.clean_value,
            "interval": [env.data_trust.interval.lower, env.data_trust.interval.upper],
        },
    }
