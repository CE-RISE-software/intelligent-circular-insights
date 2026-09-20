# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The reliability envelope: what every use case returns, in every mode.

This type is the output contract of the whole system, and it enforces it rather
than documenting it. Three invariants hold for any envelope that says ANSWER:

1. ``provenance`` is non-empty.      An answer nobody can check is not an answer.
2. grounding does not report unresolved claims.
                                     The enforced form of evidence-before-generation:
                                     an answer containing a claim that resolves to
                                     nothing in the context pack cannot be built.
3. ``confidence.calibrated >= operating_point.tau``, and tau is in the response.
                                     The selective decision, with the operating
                                     point that produced it visible to an auditor.

They are checked in ``__post_init__``, so there is no route around them: not a
flag, not a subclass, not an adapter that forgets. Constructing a violating
envelope raises ``InvariantViolation``, which is a programming error and is
supposed to be loud.

An abstention carries no such requirements — but it does carry ``abstain_reason``
and the signal vector, because "why did it decline" is the question a practitioner
actually asks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ici_core.domain.claims import GroundingReport, GroundingVerdict
from ici_core.domain.confidence import Confidence, OperatingPoint
from ici_core.domain.datatrust import DataTrust
from ici_core.domain.errors import InvariantViolation
from ici_core.domain.evidence import Evidence
from ici_core.domain.ids import SignalName
from ici_core.domain.modes import BackendMode
from ici_core.domain.trace import Trace


class Decision(str, Enum):
    ANSWER = "answer"
    ABSTAIN = "abstain"


class ProvenanceKind(str, Enum):
    PASSAGE = "passage"
    FACT = "fact"
    RULE = "rule"
    TRIPLE = "triple"
    CALC_STEP = "calc_step"


@dataclass(frozen=True)
class ProvenanceLink:
    """A pointer a reader can follow to check one part of an answer."""

    kind: ProvenanceKind
    ref: str
    source_file: str | None = None
    excerpt: str | None = None

    def __post_init__(self) -> None:
        if not self.ref:
            raise ValueError("a provenance link must have a ref")


@dataclass(frozen=True)
class QuantifiedValue:
    """A numeric answer with its unit, and optionally its uncertainty.

    Separate from the prose answer because a number that will be read by a machine
    should not have to be parsed back out of a sentence.
    """

    amount: float
    unit: str
    basis: str | None = None


@dataclass(frozen=True)
class ReliabilityEnvelope:
    """An answer with provenance, or an abstention with a reason. Never anything else."""

    decision: Decision
    mode: BackendMode
    trace: Trace
    answer: str | None = None
    value: QuantifiedValue | None = None
    evidence: tuple[Evidence, ...] = ()
    provenance: tuple[ProvenanceLink, ...] = ()
    confidence: Confidence = field(default_factory=Confidence)
    operating_point: OperatingPoint = field(default_factory=OperatingPoint)
    grounding: GroundingReport = field(default_factory=GroundingReport.not_applicable)
    data_trust: DataTrust | None = None
    abstain_reason: str | None = None
    weak_signal: SignalName | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.decision is Decision.ANSWER:
            self._check_answer_invariants()
        else:
            self._check_abstention_is_explained()

    # -- invariants ---------------------------------------------------------
    def _check_answer_invariants(self) -> None:
        if not self.provenance:
            raise InvariantViolation(
                "an ANSWER envelope must carry at least one provenance link; "
                "an answer nobody can check is not an answer"
            )
        if self.grounding.verdict is GroundingVerdict.UNRESOLVED_CLAIMS:
            raise InvariantViolation(
                f"an ANSWER envelope cannot carry unresolved claims "
                f"({len(self.grounding.unresolved)} unresolved); the caller should "
                f"have abstained"
            )
        if self.answer is not None:
            if not self.answer.strip():
                raise InvariantViolation("a prose answer cannot be empty")
            if self.grounding.verdict is not GroundingVerdict.FULLY_GROUNDED:
                raise InvariantViolation("a prose answer must be fully grounded")
        if self.confidence.calibrated < self.operating_point.tau:
            raise InvariantViolation(
                f"calibrated confidence {self.confidence.calibrated:.4f} is below "
                f"tau {self.operating_point.tau:.4f}; the selective layer should "
                f"have abstained"
            )
        if self.answer is None and self.value is None:
            raise InvariantViolation("an ANSWER envelope must carry an answer or a value")

    def _check_abstention_is_explained(self) -> None:
        if not self.abstain_reason:
            raise InvariantViolation(
                "an ABSTAIN envelope must say why; 'I don't know' without a reason "
                "is not actionable for a practitioner"
            )

    # -- constructors -------------------------------------------------------
    @classmethod
    def answered(
        cls,
        *,
        mode: BackendMode,
        trace: Trace,
        provenance: tuple[ProvenanceLink, ...],
        confidence: Confidence,
        operating_point: OperatingPoint,
        grounding: GroundingReport,
        answer: str | None = None,
        value: QuantifiedValue | None = None,
        evidence: tuple[Evidence, ...] = (),
        data_trust: DataTrust | None = None,
        warnings: tuple[str, ...] = (),
    ) -> ReliabilityEnvelope:
        return cls(
            decision=Decision.ANSWER,
            mode=mode,
            trace=trace,
            answer=answer,
            value=value,
            evidence=evidence,
            provenance=provenance,
            confidence=confidence,
            operating_point=operating_point,
            grounding=grounding,
            data_trust=data_trust,
            warnings=warnings,
        )

    @classmethod
    def abstained(
        cls,
        *,
        mode: BackendMode,
        trace: Trace,
        reason: str,
        confidence: Confidence | None = None,
        operating_point: OperatingPoint | None = None,
        grounding: GroundingReport | None = None,
        evidence: tuple[Evidence, ...] = (),
        warnings: tuple[str, ...] = (),
    ) -> ReliabilityEnvelope:
        conf = confidence or Confidence()
        return cls(
            decision=Decision.ABSTAIN,
            mode=mode,
            trace=trace,
            evidence=evidence,
            confidence=conf,
            operating_point=operating_point or OperatingPoint(),
            grounding=grounding or GroundingReport.not_applicable(),
            abstain_reason=reason,
            weak_signal=conf.signals.weakest(),
            warnings=warnings,
        )

    # -- convenience --------------------------------------------------------
    @property
    def answered_ok(self) -> bool:
        return self.decision is Decision.ANSWER
