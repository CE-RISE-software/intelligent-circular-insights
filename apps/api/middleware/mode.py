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
from dataclasses import dataclass

from ici_core.domain.modes import DEFAULT_MODE, BackendMode

LOG = logging.getLogger("ici.mode")

HEADER = "X-Backend-Mode"
RESPONSE_HEADER = "X-Backend-Mode-Used"


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
