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
    profile: str | None = Field(
        default=None,
        description="Omit to use whatever the bound mode checks against by default.",
    )


def _profile(req_profile: str | None, bundle: ProviderBundle) -> ProfileId:
    """The named profile, or whatever the bound mode checks by default.

    Not a literal default on the request model: what "no profile given" means is a
    property of the schemas this mode mounted, and CE-RISE mode mounts more of them.
    """
    return ProfileId(req_profile) if req_profile else bundle.schemas.default_profile()


@router.post("")
def synthesize(
    req: SynthesizeRequest,
    response: Response,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    llm: Annotated[LLMRequest, Depends(get_llm_request)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    correlation_id = CorrelationId(x_correlation_id or "anonymous")
    profile = _profile(req.profile, bundle)
    record, result = SynthesizeRecord(bundle, llm.records).detailed(
        req.seed,
        profile,
        correlation_id=correlation_id,
    )
    return {
        "mode": bundle.mode.value,
        "dpp_id": str(record.dpp_id),
        "record": dict(record.payload),
        # What was applied, not what was asked for: in a mode that routes, those
        # differ, and naming the request would tell a reader their record conforms
        # to a profile nothing checked it against.
        "profile": record.applied_schemas[0],
        # True by construction: the use case raises rather than returning a record
        # that does not conform. Reported anyway, because a client should not have
        # to know that to read the response.
        "conforms": True,
        "applied_schemas": list(record.applied_schemas),
        "support": [asdict(s) for s in result.support],
        "trace": record_trace(bundle, correlation_id, llm, response),
    }
