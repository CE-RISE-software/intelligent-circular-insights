# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Carbon assessment.

Thin by design: parse, delegate to the bound ``ImpactEngine``, serialise. A router
that contains logic is a router that behaves differently per mode, which is the
thing this architecture is built to avoid.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle
from ici_core.domain.ids import CorrelationId
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.usecases.assess_impact import MEASURED_SHARE, AssessImpact
from ici_core.usecases.deps import ProviderBundle
from ici_core.usecases.explain_answer import ExplainAnswer

router = APIRouter(prefix="/carbon", tags=["carbon"])


class CarbonRequest(BaseModel):
    product_id: str = Field(min_length=1)
    indicator: str = "climate_change"
    functional_unit: str | None = None
    include_trace: bool = True


@router.get("/subjects")
def subjects(bundle: Annotated[ProviderBundle, Depends(get_bundle)]) -> dict[str, Any]:
    """What this mode can assess.

    The window asks rather than hard-coding, so switching backends changes the
    picker as well as the arithmetic — Normal lists product profiles, CE-RISE the
    studies the graph declares.
    """
    return {
        "mode": bundle.mode.value,
        "subjects": [{"id": s.id, "kind": s.kind} for s in bundle.impact.subjects()],
    }


@router.post("/calculate")
def calculate(
    req: CarbonRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Assess, and report the data quality alongside the number.

    Goes through ``AssessImpact`` rather than calling the engine directly. Until
    Sprint 3 this router reached past the use-case layer straight into the port —
    which worked, and meant the layer was an empty claim: four of six use cases were
    ``NotImplementedError`` stubs and nothing failed, because nothing called them.

    The envelope is where the data-quality reading comes from. The contribution
    payload below is unchanged, so no client breaks.
    """
    envelope, result = AssessImpact(bundle).detailed(
        SubjectRef(id=req.product_id),
        ImpactRequest(indicator=req.indicator, functional_unit=req.functional_unit),
        correlation_id=CorrelationId(x_correlation_id or "anonymous"),
    )
    payload: dict[str, Any] = {
        "mode": bundle.mode.value,
        "product_id": result.subject.id,
        "indicator": result.indicator,
        "total": result.total,
        "unit": result.unit,
        "functional_unit": result.functional_unit,
        "contributions": [
            {
                "label": c.label,
                "amount": c.amount,
                "unit": c.unit,
                "share": c.share,
                # Badged so a reader is never misled about which numbers are
                # measured and which are inferred.
                "is_proxy": c.is_proxy,
            }
            for c in result.contributions
        ],
        "uncertainty": list(result.uncertainty) if result.uncertainty else None,
        "diagnostics": list(result.diagnostics),
        "uses_proxy_factors": result.uses_proxy_factors,
        # The contribution-weighted share resting on measured rather than inferred
        # inputs. Not a calibrated probability and not comparable with a search
        # result's confidence — named so nothing can average the two.
        "measured_share": envelope.confidence.signals.values.get(MEASURED_SHARE),
    }
    if req.include_trace:
        # Taken from the envelope rather than asking the engine again: one
        # assessment, one derivation, no chance of two views disagreeing.
        payload["provenance"] = [
            {
                "kind": link.kind.value,
                "ref": link.ref,
                "source_file": link.source_file,
                "excerpt": link.excerpt,
            }
            for link in envelope.provenance
        ]
        payload["arithmetic"] = ExplainAnswer(bundle)(envelope, "total").arithmetic
        payload["trace"] = [{"name": s.name, "detail": s.detail} for s in envelope.trace.steps]
    return payload
