# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Building a passport from a few supplied facts.

The strictest endpoint in the service, and the one where that matters most: a
passport is a compliance document, and a plausible invalid one is worse than none
at all. So the record is generated, grounded field by field against retrieved
evidence, then checked again against the *bound* profile — and a failure at any of
those three points is a typed 422 with the reason, never a record with a caveat
attached.

Unlike ``/validate/repair``, this has no "suggestions" escape hatch. Repair is
mending a document somebody else wrote and can review; synthesis is writing one
from nothing, where an unverified field has no author to answer for it.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Response
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle, get_llm_request
from apps.api.record_audit import record_trace
from ici_core.domain.ids import CorrelationId, ProfileId
from ici_core.usecases.deps import ProviderBundle
from ici_core.usecases.synthesize_record import SynthesizeRecord
from ici_llm.runtime import LLMRequest

router = APIRouter(prefix="/synthesize", tags=["synthesize"])


class SynthesizeRequest(BaseModel):
    seed: dict[str, Any] = Field(
        description=(
            "The facts you already have. Everything else must be grounded in "
            "retrievable evidence about this product, or the request is declined."
        )
    )
    profile: str = "eu-dpp"


@router.post("")
def synthesize(
    req: SynthesizeRequest,
    response: Response,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    llm: Annotated[LLMRequest, Depends(get_llm_request)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    correlation_id = CorrelationId(x_correlation_id or "anonymous")
    record, result = SynthesizeRecord(bundle, llm.records).detailed(
        req.seed,
        ProfileId(req.profile),
        correlation_id=correlation_id,
    )
    return {
        "mode": bundle.mode.value,
        "dpp_id": str(record.dpp_id),
        "record": dict(record.payload),
        "profile": str(ProfileId(req.profile)),
        # True by construction: the use case raises rather than returning a record
        # that does not conform. Reported anyway, because a client should not have
        # to know that to read the response.
        "conforms": True,
        "applied_schemas": list(record.applied_schemas),
        "support": [asdict(s) for s in result.support],
        "trace": record_trace(bundle, correlation_id, llm, response),
    }
