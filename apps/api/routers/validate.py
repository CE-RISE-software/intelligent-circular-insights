# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Conformance checking against a schema profile."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from apps.api.deps import get_bundle
from ici_core.domain.ids import DppId, ProfileId
from ici_core.domain.record import DPPRecord
from ici_core.usecases.deps import ProviderBundle

router = APIRouter(prefix="/validate", tags=["validate"])


class ValidateRequest(BaseModel):
    dpp: dict[str, Any]
    profile: str = "eu-dpp"


@router.post("")
def validate(
    req: ValidateRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    record = DPPRecord(dpp_id=DppId(str(req.dpp.get("dpp_id", "unidentified"))), payload=req.dpp)
    report = bundle.schemas.conform(record, ProfileId(req.profile))
    return {
        "mode": bundle.mode.value,
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


@router.get("/profiles")
def profiles(
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
) -> dict[str, Any]:
    return {
        "mode": bundle.mode.value,
        "profiles": [
            {"id": str(p.id), "title": p.title, "layer": p.layer, "version": p.version}
            for p in bundle.schemas.profiles()
        ],
    }
