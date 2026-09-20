# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Conservative request-local call/token reservations, including failed calls."""

from __future__ import annotations

from dataclasses import dataclass

from ici_llm.errors import BudgetExceeded
from ici_llm.prompts import canonical
from ici_llm.transport import Request


@dataclass
class RequestBudget:
    max_calls: int = 8
    max_reserved_tokens: int = 100_000
    calls: int = 0
    reserved_tokens: int = 0

    def reserve(self, request: Request) -> None:
        # UTF-8 bytes conservatively bound text tokens; add framing headroom.
        output = request.kwargs.get(
            "max_completion_tokens", request.kwargs.get("max_output_tokens", 0)
        )
        required = len(canonical(request.kwargs).encode()) + output + 256
        if (
            self.calls >= self.max_calls
            or self.reserved_tokens + required > self.max_reserved_tokens
        ):
            raise BudgetExceeded("The request's model call/token budget was exhausted.")
        self.calls += 1
        self.reserved_tokens += required
