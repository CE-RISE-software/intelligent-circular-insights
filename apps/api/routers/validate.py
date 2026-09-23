# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Conformance checking, and evidence-backed repair.

Two endpoints with a deliberate asymmetry. ``/validate`` is deterministic, free and
always available. ``/validate/repair`` can cost a model call and therefore decline
when the deployment has language-model assistance off or replay has no response.
Without source evidence, only separate review suggestions may use model priors.

The repair response keeps four things apart that a single "repaired record" field
would silently merge: what was filled from evidence, what could not be grounded,
what the model proposed and was rejected, and what it suggests for human review.
ADR 0011 is the reason; the short version is that an unverified guess presented as
validated data is the failure this system exists to prevent, and a response shape
that makes it easy to conflate them is where that failure starts.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Response
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle, get_llm_request
from apps.api.record_audit import record_trace
from ici_core.domain.ids import CorrelationId, DppId, ProfileId
from ici_core.domain.record import DPPRecord
from ici_core.usecases.deps import ProviderBundle
from ici_core.usecases.synthesize_record import SynthesizeRecord
from ici_core.usecases.validate_record import ValidateRecord
from ici_llm.runtime import LLMRequest

router = APIRouter(prefix="/validate", tags=["validate"])


class ValidateRequest(BaseModel):
    dpp: dict[str, Any]
    profile: str | None = Field(
        default=None,
        description="Omit to use whatever the bound mode checks against by default.",
    )


class RepairRequest(BaseModel):
    dpp: dict[str, Any]
    profile: str | None = Field(
        default=None,
        description="Omit to use whatever the bound mode checks against by default.",
    )
    suggest_from_training: bool = Field(
        default=True,
        description=(
            "Include model-prior candidates for human review. They are returned in a "
            "separate field, are never applied to the record, and are never evidence."
        ),
    )


def _profile(req_profile: str | None, bundle: ProviderBundle) -> ProfileId:
    """The named profile, or whatever the bound mode checks by default.

    Not a literal default on the request model: what "no profile given" means is a
    property of the schemas this mode mounted, and CE-RISE mode mounts more of them.
    """
    return ProfileId(req_profile) if req_profile else bundle.schemas.default_profile()


def _record(payload: dict[str, Any]) -> DPPRecord:
    return DPPRecord(dpp_id=DppId(str(payload.get("dpp_id", "unidentified"))), payload=payload)


def _report(report: Any) -> dict[str, Any]:
    return {
        "profile": str(report.profile),
        "conforms": report.conforms,
        "checked_paths": report.checked_paths,
        # Typed and located. A bare boolean is useless to whoever has to repair it.
        "violations": [
            {
                "kind": v.kind.value,
                "location": v.location,
                "message": v.message,
                "expected": v.expected,
                "actual": v.actual,
            }
            for v in report.violations
        ],
    }


@router.post("")
def validate(
    req: ValidateRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    report = ValidateRecord(bundle)(
        _record(req.dpp),
        _profile(req.profile, bundle),
        correlation_id=CorrelationId(x_correlation_id or "anonymous"),
    )
    return {"mode": bundle.mode.value, **_report(report)}


@router.post("/repair")
def repair(
    req: RepairRequest,
    response: Response,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    llm: Annotated[LLMRequest, Depends(get_llm_request)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    correlation_id = CorrelationId(x_correlation_id or "anonymous")
    profile = _profile(req.profile, bundle)
    result = SynthesizeRecord(bundle, llm.records).repair(
        req.dpp,
        profile,
        correlation_id=correlation_id,
        suggest_from_training=req.suggest_from_training,
    )

    # Re-checked against the bound profile rather than trusting the composer's own
    # verdict: the composer validates against the schema it was built with, and a
    # deployment may have bound a stricter one.
    after = bundle.schemas.conform(_record(result.record), profile)

    return {
        "mode": bundle.mode.value,
        "record": result.record,
        "conforms": after.conforms,
        "after": _report(after),
        # Each field was filled from a specific piece of evidence, named here.
        "grounded_fills": [
            {
                "path": f.path,
                "value": f.value,
                "evidence_id": f.support.evidence_id,
                "evidence_ref": f.support.evidence_ref,
                "source_pointer": f.support.source_pointer,
                # A model feature, not a calibrated probability. Named as such in
                # the payload so a client cannot compare it with a search result's.
                "model_score": f.confidence,
            }
            for f in result.fills
        ],
        "cannot_be_grounded": [
            {"path": i.path, "reason": i.reason} for i in result.cannot_be_grounded
        ],
        "rejected": [{"path": i.path, "reason": i.reason} for i in result.rejected],
        # Separate, and flagged at every level: a different key, an explicit status,
        # and requires_review on each item. Anything that renders these alongside
        # grounded_fills without saying so is misreporting them.
        "unverified_suggestions": [
            {
                "path": s.path,
                "value": s.value,
                "rationale": s.rationale,
                "model_score": s.confidence,
                "source": s.source,
                "status": s.status,
                "requires_review": s.requires_review,
            }
            for s in result.suggestions
        ],
        "trace": record_trace(bundle, correlation_id, llm, response),
    }


@router.get("/profiles")
def profiles(
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    return {
        "mode": bundle.mode.value,
        # Named, not implied by ordering: the window has to show which profile a
        # record is checked against when the user picks none, and that answer is the
        # mode's, not the client's. Hard-coding "eu-dpp" in the UI is how switching
        # backend left Validate checking the old schema.
        "default": str(bundle.schemas.default_profile()),
        "profiles": [
            {"id": str(p.id), "title": p.title, "layer": p.layer, "version": p.version}
            for p in bundle.schemas.profiles()
        ],
    }
