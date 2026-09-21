# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Search & Answer — the reliability path.

The four published stages plus the grounding check, orchestrated by
``AnswerQuestion`` in the core. This router only translates HTTP to domain types
and back, so the same inference path serves both modes.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle
from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.ids import CorrelationId, ProductId
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.usecases.answer_question import AnswerQuestion
from ici_core.usecases.deps import ProviderBundle

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    q: str = Field(min_length=1)
    product: str | None = None
    domain: str | None = None
    session: str | None = "default"
    tau: float | None = None
    top_k_documents: int = 4
    top_k_memory: int = 3


@router.post("")
def search(
    req: SearchRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
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
    envelope = AnswerQuestion(bundle)(
        query,
        budget=RetrievalBudget(top_k_documents=req.top_k_documents, top_k_memory=req.top_k_memory),
        point=OperatingPoint(tau=req.tau if req.tau is not None else 0.5),
    )
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
            "steps": [{"name": s.name, "detail": s.detail} for s in env.trace.steps],
        },
        "data_trust": None
        if env.data_trust is None
        else {
            "clean_value": env.data_trust.clean_value,
            "interval": [env.data_trust.interval.lower, env.data_trust.interval.upper],
        },
    }
