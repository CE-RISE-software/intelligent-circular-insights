# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Claims, and whether each one is actually supported.

A composed answer is decomposed into claims so that each can be resolved against
the context pack. This is what turns "evidence before generation" from a prompt
instruction into a check (ARCHITECTURE.md §9.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ici_core.domain.ids import ClaimId, EvidenceId


@dataclass(frozen=True)
class Claim:
    """One assertion extracted from an answer, with the evidence it cites."""

    id: ClaimId
    text: str
    cited: tuple[EvidenceId, ...] = ()

    @property
    def cites_anything(self) -> bool:
        return bool(self.cited)


class GroundingVerdict(str, Enum):
    FULLY_GROUNDED = "fully_grounded"
    """Every claim resolved to evidence present in the pack."""

    UNRESOLVED_CLAIMS = "unresolved_claims"
    """At least one claim cited nothing, or cited an id not in the pack."""

    NOT_APPLICABLE = "not_applicable"
    """There was nothing to verify: a deterministic result with no composed prose."""


@dataclass(frozen=True)
class GroundingReport:
    """The outcome of checking an answer against the pack."""

    claims_total: int
    claims_resolved: int
    unresolved: tuple[Claim, ...] = ()
    verdict: GroundingVerdict = GroundingVerdict.NOT_APPLICABLE

    def __post_init__(self) -> None:
        if any(type(n) is not int or n < 0 for n in (self.claims_total, self.claims_resolved)):
            raise ValueError("claim counts must be nonnegative integers")
        if self.claims_resolved > self.claims_total:
            raise ValueError("resolved claims cannot exceed total claims")
        if self.verdict is GroundingVerdict.FULLY_GROUNDED and self.unresolved:
            raise ValueError("fully grounded report cannot list unresolved claims")
        if self.verdict is GroundingVerdict.UNRESOLVED_CLAIMS and not self.unresolved:
            raise ValueError("unresolved verdict must name the unresolved claims")
        if self.verdict is GroundingVerdict.FULLY_GROUNDED:
            if self.claims_total == 0 or self.claims_resolved != self.claims_total:
                raise ValueError(
                    "fully grounded report must resolve every claim, with at least one"
                )
        elif self.verdict is GroundingVerdict.UNRESOLVED_CLAIMS:
            if self.claims_total - self.claims_resolved != len(self.unresolved):
                raise ValueError("unresolved claim count must match the report")
        elif self.verdict is GroundingVerdict.NOT_APPLICABLE:
            if self.claims_total or self.claims_resolved or self.unresolved:
                raise ValueError("not-applicable grounding cannot contain claims")
        else:
            raise ValueError("unknown grounding verdict")

    @classmethod
    def not_applicable(cls) -> GroundingReport:
        """For deterministic paths — a carbon calculation composes no prose."""
        return cls(claims_total=0, claims_resolved=0, verdict=GroundingVerdict.NOT_APPLICABLE)

    @property
    def blocks_answering(self) -> bool:
        return self.verdict is GroundingVerdict.UNRESOLVED_CLAIMS
