# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The CE-RISE data-model catalogue and its routing."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from apps.api.deps import get_bundle
from ici_core.usecases.deps import ProviderBundle

router = APIRouter(prefix="/ce-rise-models", tags=["ce-rise-models"])


class RouteRequest(BaseModel):
    question: str


@router.get("/catalog")
def catalog(bundle: Annotated[ProviderBundle, Depends(get_bundle)]) -> dict[str, Any]:
    registry = bundle.substrates
    models = getattr(registry, "models", ())
    return {
        "mode": bundle.mode.value,
        "source_org": "https://codeberg.org/CE-RISE-models",
        # The models are CC-BY-NC-4.0 while this code is EUPL-1.2, so the licence
        # travels with the data rather than being implied by the repository root.
        "licence": "CC-BY-NC-4.0",
        "model_count": len(models),
        "models": [
            {
                "id": m.id,
                "title": m.title,
                "layer": m.layer,
                "summary": m.summary,
                "url": m.url,
                "keywords": list(m.keywords),
            }
            for m in models
        ],
    }


@router.post("/route")
def route(
    req: RouteRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    registry = bundle.substrates
    hits = registry.route(req.question) if hasattr(registry, "route") else ()
    return {
        "mode": bundle.mode.value,
        "question": req.question,
        "matches": [
            {"id": m.id, "title": m.title, "layer": m.layer, "score": m.matches(req.question)}
            for m in hits
        ],
    }


@router.get("/coverage")
def coverage(bundle: Annotated[ProviderBundle, Depends(get_bundle)]) -> dict[str, Any]:
    """Fire rate and conditional precision per mounted substrate (ADR 0005).

    The instrument, not the study: pointing it at a corpus to publish a coverage
    claim is a separate exercise.
    """
    report = bundle.substrates.coverage_report()
    return {
        "mode": bundle.mode.value,
        "substrates": [
            {
                "substrate": str(c.substrate),
                "questions_seen": c.questions_seen,
                "questions_fired": c.questions_fired,
                "fire_rate": c.fire_rate,
                "conditional_precision": c.conditional_precision,
            }
            for c in report.per_substrate
        ],
    }
