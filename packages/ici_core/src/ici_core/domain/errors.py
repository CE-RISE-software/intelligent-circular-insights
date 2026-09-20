# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Typed domain errors.

Every one of these maps to a specific HTTP status in exactly one place
(``apps/api/errors.py``). Nothing in the domain raises a bare ``Exception``, and
nothing catches one to hide it.
"""

from __future__ import annotations


class IciError(Exception):
    """Base for every error this system raises deliberately."""


class GenerationError(IciError):
    """A model could not supply a complete, usable answer.

    Adapters provide specific subclasses. The core catches this type to abstain
    without depending on an SDK or returning a partial answer.
    Cassette misses are deliberately NOT generation errors: they must fail tests.
    """


class CapabilityError(IciError):
    """The active mode cannot serve this request.

    Not a failure — an honest answer. A mode that lacks a substrate, an engine or
    a schema profile says so with a reason, and the API returns 422. Returning 500
    here would be a lie about whose fault it is.
    """

    def __init__(self, capability: str, mode: str, reason: str) -> None:
        self.capability = capability
        self.mode = mode
        self.reason = reason
        super().__init__(f"{mode!r} cannot serve {capability!r}: {reason}")


class InvariantViolation(IciError):
    """A response was constructed that breaks one of the envelope invariants.

    This is always a programming error, never a user error. It exists so the
    invariant cannot be quietly bypassed by an adapter that forgets provenance.
    """


class SubstrateUnavailable(IciError):
    """A substrate failed to mount or is not mounted in this bundle."""

    def __init__(self, substrate_id: str, reason: str) -> None:
        self.substrate_id = substrate_id
        self.reason = reason
        super().__init__(f"substrate {substrate_id!r} unavailable: {reason}")


class BudgetExceeded(IciError):
    """A per-request cost or step ceiling was hit.

    Raised rather than looping. A runaway agent loop is a bill, and a bill is a bug.
    """
