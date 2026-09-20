"""PEF Studio — the WP3 integration.

Only mounted usefully in CE-RISE mode. In Normal mode the substrate is a schema
catalogue with no graph behind it, so these endpoints answer with a typed 422
rather than pretending.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle
from ici_core.domain.errors import CapabilityError
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.usecases.deps import ProviderBundle

router = APIRouter(prefix="/pef", tags=["pef"])


class CalculateRequest(BaseModel):
    study_id: str | None = None
    scenario: dict[str, str] = Field(default_factory=dict)


class SparqlRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int | None = None


def _graph_registry(bundle: ProviderBundle) -> Any:
    registry = bundle.substrates
    if not hasattr(registry, "run_all_questions"):
        raise CapabilityError(
            capability="PEF studio",
            mode=bundle.mode.value,
            reason="no knowledge graph is mounted in this mode; switch to ce-rise",
        )
    return registry


@router.get("/overview")
def overview(bundle: Annotated[ProviderBundle, Depends(get_bundle)]) -> dict[str, Any]:
    registry = _graph_registry(bundle)
    graph = registry.graph
    summary = registry.coverage_summary()
    return {
        "mode": bundle.mode.value,
        "graph": {
            "triples": len(graph.graph),
            "activities": len(graph.activities),
            "datasets": len(graph.datasets),
            "studies": graph.studies(),
        },
        "competency_questions": {
            "live": summary.live,
            "answered": summary.answered,
            # Stated against the paper's full set rather than only what works, so
            # coverage is a number a reader can judge.
            "total_in_paper": summary.total_in_paper,
            "share_of_paper": round(summary.share_of_paper, 4),
        },
        "compliance_note": (
            "Background flows use a documented proxy factor pack, not licensed data. "
            "This is not an EF-compliant declaration."
        ),
    }


@router.post("/calculate")
def calculate(
    req: CalculateRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    registry = _graph_registry(bundle)
    result = registry.impact.assess(
        SubjectRef(id=req.study_id or "", kind="study"),
        ImpactRequest(indicator="climate_change", scenario=req.scenario),
    )
    return {
        "mode": bundle.mode.value,
        "functional_unit": result.functional_unit,
        "total": result.total,
        "unit": result.unit,
        "data_quality": result.data_quality,
        "by_stage": [
            {"stage": c.label, "amount": c.amount, "share": c.share, "is_proxy": c.is_proxy}
            for c in result.contributions
        ],
        "uncertainty": list(result.uncertainty) if result.uncertainty else None,
        "diagnostics": list(result.diagnostics),
        "uses_proxy_factors": result.uses_proxy_factors,
    }


@router.get("/competency-questions")
def competency_questions(
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    registry = _graph_registry(bundle)
    return {
        "mode": bundle.mode.value,
        "total_in_paper": registry.coverage_summary().total_in_paper,
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "pef_requirement": q.pef_requirement,
                "why_it_matters": q.why_it_matters,
            }
            for q in registry.questions
        ],
    }


@router.post("/competency-questions/{question_id}")
def run_competency_question(
    question_id: str,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    result = _graph_registry(bundle).run_question(question_id)
    return {
        "mode": bundle.mode.value,
        "id": result.question.id,
        "question": result.question.question,
        "pef_requirement": result.question.pef_requirement,
        "sparql": result.question.sparql,
        "answered": result.answered,
        "rows": list(result.rows),
        "error": result.error,
    }


@router.post("/sparql")
def sparql(
    req: SparqlRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    """Read-only. Update operations and federation are refused before execution."""
    from ici_substrates.pefdpp.sparql import UnsafeQueryError

    registry = _graph_registry(bundle)
    try:
        payload = registry.query(req.query, limit=req.limit)
    except UnsafeQueryError as exc:
        raise CapabilityError(capability="SPARQL", mode=bundle.mode.value, reason=str(exc)) from exc
    return {"mode": bundle.mode.value, **payload}
