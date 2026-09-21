# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Resolving which backend serves a request.

Precedence, highest first: the ``X-Backend-Mode`` header, a session pin, the
deployment default, the hard default. Mirrors the ``X-Model`` convention the
Settings panel already uses, so the frontend pattern is unchanged.

An unrecognised value falls back to the default and warns rather than failing the
request. A typo in a header should not be an outage, and the response says which
mode actually ran, so nothing is hidden by the leniency.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ici_core.domain.modes import DEFAULT_MODE, BackendMode

LOG = logging.getLogger("ici.mode")

HEADER = "X-Backend-Mode"
RESPONSE_HEADER = "X-Backend-Mode-Used"
SOURCE_HEADER = "X-Backend-Mode-Source"
WARNING_HEADER = "X-Backend-Mode-Warning"


@dataclass(frozen=True)
class ModeResolution:
    mode: BackendMode
    source: str
    warning: str | None = None


@dataclass(frozen=True)
class ModeResolver:
    """Turns the request's various hints into one mode, and says where it came from."""

    default: BackendMode = DEFAULT_MODE
    allowed: tuple[BackendMode, ...] = (BackendMode.NORMAL, BackendMode.CE_RISE)

    def resolve(self, header: str | None = None, session_pin: str | None = None) -> ModeResolution:
        for raw, source in ((header, "header"), (session_pin, "session")):
            if raw is None or not raw.strip():
                continue
            parsed = BackendMode.parse(raw)
            if parsed is None:
                warning = f"unknown backend mode {raw!r}; falling back to {self.default.value!r}"
                LOG.warning(warning)
                return ModeResolution(self.default, "default", warning)
            if parsed not in self.allowed:
                warning = (
                    f"backend mode {parsed.value!r} is not enabled here; "
                    f"falling back to {self.default.value!r}"
                )
                LOG.warning(warning)
                return ModeResolution(self.default, "default", warning)
            return ModeResolution(parsed, source)
        return ModeResolution(self.default, "default")


class ModeMiddleware(BaseHTTPMiddleware):
    """Resolves the mode once per request and stamps it on the way out.

    Two jobs, and the second is the reason this is middleware rather than a
    dependency. Resolution is stashed on ``request.state`` so the dependency graph
    and the response header cannot disagree — a badge that reads one value while
    another backend served the request is the specific failure this design rules
    out.

    The header is set on *every* response, including the 422 a mode returns when it
    cannot serve a feature. An honest decline still has to say who declined.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        resolver: ModeResolver | None = getattr(request.app.state, "mode_resolver", None)
        if resolver is None:  # pragma: no cover - only before lifespan has run
            return await call_next(request)

        resolution = resolver.resolve(header=request.headers.get(HEADER))
        request.state.mode_resolution = resolution

        response = await call_next(request)
        response.headers[RESPONSE_HEADER] = resolution.mode.value
        response.headers[SOURCE_HEADER] = resolution.source
        if resolution.warning:
            # A typo in a header is not an outage, but it is not invisible either.
            response.headers[WARNING_HEADER] = resolution.warning
        return response
