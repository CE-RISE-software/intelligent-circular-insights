# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Record assistance results: evidence-backed changes and unverified guesses stay apart."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


def same_product(seed: Mapping[str, Any], record: Mapping[str, Any]) -> bool:
    left, right = seed.get("product"), record.get("product")
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    if left.get("id"):
        return left["id"] == right.get("id") and all(
            left[k] == right.get(k) for k in ("brand", "model") if left.get(k)
        )
    return all(left.get(k) and left[k] == right.get(k) for k in ("brand", "model"))


@dataclass(frozen=True)
class RecordIssue:
    path: str
    reason: str


@dataclass(frozen=True)
class ValueSupport:
    path: str
    evidence_id: str
    evidence_ref: str
    source_pointer: str


@dataclass(frozen=True)
class GroundedFill:
    path: str
    value: Any
    support: ValueSupport
    confidence: float


@dataclass(frozen=True)
class UnverifiedSuggestion:
    path: str
    value: Any
    rationale: str
    confidence: float
    source: str = "model_training"
    status: str = "unverified"
    requires_review: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 0.3:
            raise ValueError("unverified model scores must be between 0 and 0.3")
        if (self.source, self.status, self.requires_review) != (
            "model_training",
            "unverified",
            True,
        ):
            raise ValueError("model-training suggestions must remain unverified and for review")


@dataclass(frozen=True)
class RepairResult:
    record: dict[str, Any]
    fills: tuple[GroundedFill, ...]
    cannot_be_grounded: tuple[RecordIssue, ...]
    rejected: tuple[RecordIssue, ...] = ()
    suggestions: tuple[UnverifiedSuggestion, ...] = ()

    @property
    def conforms(self) -> bool:
        return not self.cannot_be_grounded


@dataclass(frozen=True)
class SynthesisResult:
    record: dict[str, Any]
    support: tuple[ValueSupport, ...]
