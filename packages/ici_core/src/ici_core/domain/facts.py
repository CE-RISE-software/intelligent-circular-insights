# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Persistent facts, and what it takes to store one.

The published memory prototype is session-scoped and stores whatever it is given.
This model encodes the four properties §4.2 of the paper lists as missing:
product scope, validation before storage, supersession rather than mutation, and
a readable correction history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ici_core.domain.ids import FactId, ProductId


class ValidationOutcome(str, Enum):
    """Whether a fact may be stored at all."""

    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Fact:
    """A validated statement about a product, with provenance and a timestamp."""

    subject: str
    predicate: str
    value: str
    product_id: ProductId
    provenance_ref: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def __post_init__(self) -> None:
        if not self.provenance_ref:
            raise ValueError("a fact without provenance may not be stored")
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware")


@dataclass(frozen=True)
class FactVersion:
    """One entry in a correction chain.

    A correction appends a new version and points at the one it replaces. Nothing
    is mutated and nothing is deleted, so 'what did we believe, and when' stays
    answerable.
    """

    id: FactId
    fact: Fact
    supersedes: FactId | None = None
    reason: str | None = None

    @property
    def is_correction(self) -> bool:
        return self.supersedes is not None
