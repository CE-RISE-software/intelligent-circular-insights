# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""FastAPI application factory.

Bundles are built in the lifespan handler, once, before the first request. That
is deliberate: a mode switch should be a dictionary lookup, and a graph that loads
lazily on first use makes one unlucky user pay for everyone.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from apps.api import errors
from apps.api.bundles import build_registry
from apps.api.middleware.mode import RESPONSE_HEADER, ModeResolver
from apps.api.settings import Settings, get_settings
from ici_core.domain.modes import DEFAULT_MODE, BackendMode

LOG = logging.getLogger("ici")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    modes = tuple(m for m in (BackendMode.parse(name) for name in settings.allowed_modes) if m)
    app.state.registry = build_registry(modes, settings)
    app.state.mode_resolver = ModeResolver(
        default=BackendMode.parse(settings.backend_mode_default) or DEFAULT_MODE,
        allowed=modes,
    )
    LOG.info("bundles built: %s", ", ".join(m.value for m in app.state.registry.available()))
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )

    app = FastAPI(
        title="Intelligent Circular Insights",
        version="0.1.0",
        description=(
            "Reliability-first question answering over product records. "
            "Every output is an evidence-grounded answer with provenance, or an "
            "explicit abstention."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings

    from apps.api.routers import carbon, models, pef, search, validate

    for module in (search, carbon, validate, models, pef):
        app.include_router(module.router, prefix="/api")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Model", "X-Backend-Mode"],
        expose_headers=["X-Model-Used", RESPONSE_HEADER],
    )
    errors.install(app)

    @app.get("/api/health", tags=["service"])
    def health() -> dict[str, Any]:
        registry = getattr(app.state, "registry", None)
        available = [m.value for m in registry.available()] if registry else []
        return {"ok": True, "version": app.version, "modes_built": available}

    @app.get("/api/settings", tags=["service"])
    def read_settings(request: Request) -> dict[str, Any]:
        """What the frontend Settings panel reads on load.

        Reports the modes that were actually *built*, not the ones configured, so
        the UI cannot offer a switch that would fail.
        """
        registry = getattr(request.app.state, "registry", None)
        built = [m.value for m in registry.available()] if registry else []
        return {
            "model_default": settings.llm_model_default,
            "model_allowed": list(settings.allowed_models),
            "mode_default": settings.backend_mode_default,
            "mode_allowed": built,
            "version": app.version,
        }

    return app


app = create_app()
