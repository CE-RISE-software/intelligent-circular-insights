# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Provider failures never contain raw SDK messages, prompts or credentials."""

from ici_core.domain.errors import BudgetExceeded as BudgetExceeded
from ici_core.domain.errors import GenerationError, IciError


class RateLimited(GenerationError):
    """The provider rejected the request because of a rate limit."""


class Refused(GenerationError):
    """A refusal or content filter is an abstention, never an answer."""


class Truncated(GenerationError):
    """The completion stopped before it was complete."""


class Unavailable(GenerationError):
    """The service, credentials or requested capability are unavailable."""


class InvalidOutput(GenerationError):
    """The response is empty, malformed or violates the requested schema."""


class CassetteMiss(IciError):
    """A missing fixture is a regression, not permission to call the network."""


class CassetteCorrupt(IciError):
    """A cassette is malformed or does not match its request hash."""
