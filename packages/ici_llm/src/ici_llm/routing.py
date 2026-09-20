# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Request model selection. No environment reads or mutable process defaults."""

from __future__ import annotations

import logging
from dataclasses import dataclass

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelRouter:
    default: str = "gpt-4o-mini"
    allowed: tuple[str, ...] = ("gpt-4o-mini", "gpt-5")

    def __post_init__(self) -> None:
        if self.default not in self.allowed:
            raise ValueError("default model must be in the allowed model list")

    def resolve(self, requested: str | None = None) -> str:
        if requested is None:
            return self.default
        if requested in self.allowed:
            return requested
        LOG.warning("Unknown model requested; falling back to the configured default")
        return self.default
