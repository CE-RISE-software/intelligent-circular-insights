# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Backend modes.

A mode is a named bundle of substrates, adapters and a default operating point
(ADR 0002). The core never branches on it; it exists so a response can say which
backend answered, and so the composition root can pick an adapter set.
"""

from __future__ import annotations

from enum import Enum


class BackendMode(str, Enum):
    """Which backend served a request."""

    NORMAL = "normal"
    CE_RISE = "ce-rise"

    @classmethod
    def parse(cls, raw: str | None) -> BackendMode | None:
        """Parse a header value. Returns None for anything unrecognised.

        Deliberately lenient: an unknown mode falls back to the default with a
        warning rather than failing the request (TESTING.md edge-case table).
        """
        if raw is None:
            return None
        candidate = raw.strip().lower().replace("_", "-")
        for mode in cls:
            if mode.value == candidate:
                return mode
        return None


DEFAULT_MODE = BackendMode.NORMAL
