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
from ici_llm.errors import CassetteCorrupt, CassetteMiss


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

    @app.exception_handler(CassetteMiss)
    async def _cassette(request: Request, __: CassetteMiss) -> JSONResponse:
        """A deployment that cannot reach a model is not a server error.

        Deliberately *not* folded into an abstention. An abstention says the system
        reasoned and declined on confidence grounds; a missing cassette says this
        deployment cannot compose prose at all. Reporting the second as the first
        would put a configuration problem into the reliability statistics, which is
        the one kind of dishonesty this codebase spends the most effort avoiding.

        It was a 500 until Sprint 3, where the frontend made it visible: the Search
        window went blank, and — because an unhandled exception escapes past
        ModeMiddleware — the mode badge lost the header and went blank with it.
        """
        return JSONResponse(
            status_code=422,
            content={
                "error": "model_unavailable",
                "capability": "a composed answer",
                "mode": request.state.mode_resolution.mode.value,
                "reason": (
                    "No recorded response exists for this question and the workbench is "
                    "running in replay mode, which never calls the model. Record a "
                    "cassette (LLM_CASSETTE_MODE=record with an API key) or ask one of "
                    "the questions that has one. Everything else on this page — "
                    "retrieval, validation, both impact engines — is deterministic and "
                    "unaffected."
                ),
            },
        )

    @app.exception_handler(CassetteCorrupt)
    async def _corrupt_cassette(request: Request, _: CassetteCorrupt) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "model_unavailable",
                "capability": "a composed answer",
                "mode": request.state.mode_resolution.mode.value,
                "reason": (
                    "The recorded response is invalid. Restore the reviewed cassette "
                    "before retrying; no live fallback was attempted."
                ),
            },
        )

    @app.exception_handler(InvariantViolation)
    async def _invariant(_: Request, exc: InvariantViolation) -> JSONResponse:
        # Deliberately loud: this is always our bug, never the caller's.
        return JSONResponse(
            status_code=500,
            content={"error": "invariant_violation", "detail": str(exc)},
        )
