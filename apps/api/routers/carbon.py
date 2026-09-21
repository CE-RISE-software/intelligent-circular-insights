# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Carbon assessment.

Thin by design: parse, delegate to the bound ``ImpactEngine``, serialise. A router
that contains logic is a router that behaves differently per mode, which is the
thing this architecture is built to avoid.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.usecases.deps import ProviderBundle

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
) -> dict[str, Any]:
    subject = SubjectRef(id=req.product_id)
    result = bundle.impact.assess(
        subject, ImpactRequest(indicator=req.indicator, functional_unit=req.functional_unit)
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
    }
    if req.include_trace:
        provenance = bundle.impact.explain(result, "total")
        payload["provenance"] = [
            {
                "kind": link.kind.value,
                "ref": link.ref,
                "source_file": link.source_file,
                "excerpt": link.excerpt,
            }
            for link in provenance.links
        ]
        payload["arithmetic"] = provenance.arithmetic
    return payload
