# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The one place a domain error becomes an HTTP status.

``CapabilityError`` is 422, not 500: a mode that cannot serve a feature is giving
an honest answer about its own limits, and 500 would blame the server for a
question it was right to decline. ``InvariantViolation`` is 500, because it means
the code built a response that should have been impossible.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ici_core.domain.errors import (
    BudgetExceeded,
    CapabilityError,
    InvariantViolation,
    SubstrateUnavailable,
)


def install(app: FastAPI) -> None:
    @app.exception_handler(CapabilityError)
    async def _capability(_: Request, exc: CapabilityError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "capability_unavailable",
                "capability": exc.capability,
                "mode": exc.mode,
                "reason": exc.reason,
            },
        )

    @app.exception_handler(SubstrateUnavailable)
    async def _substrate(_: Request, exc: SubstrateUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "substrate_unavailable",
                "substrate": exc.substrate_id,
                "reason": exc.reason,
            },
        )

    @app.exception_handler(BudgetExceeded)
    async def _budget(_: Request, exc: BudgetExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429, content={"error": "budget_exceeded", "reason": str(exc)}
        )

    @app.exception_handler(InvariantViolation)
    async def _invariant(_: Request, exc: InvariantViolation) -> JSONResponse:
        # Deliberately loud: this is always our bug, never the caller's.
        return JSONResponse(
            status_code=500,
            content={"error": "invariant_violation", "detail": str(exc)},
        )
