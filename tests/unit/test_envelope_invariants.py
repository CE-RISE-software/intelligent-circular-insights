"""The three invariants, tested by trying to break them.

These are the most important tests in the repository. They assert that the failure
modes this architecture exists to prevent are *unrepresentable*, not merely
discouraged: you cannot construct an answer without provenance, an answer carrying
an unresolved claim, or an answer below its own threshold.
"""

from __future__ import annotations

import pytest

from ici_core.domain.claims import Claim, GroundingReport, GroundingVerdict
from ici_core.domain.confidence import Confidence, OperatingPoint, SignalVector
from ici_core.domain.envelope import (
    Decision,
    ProvenanceKind,
    ProvenanceLink,
    ReliabilityEnvelope,
)
from ici_core.domain.errors import InvariantViolation
from ici_core.domain.ids import ClaimId, CorrelationId, SignalName
from ici_core.domain.modes import BackendMode
from ici_core.domain.trace import Trace

TRACE = Trace(correlation_id=CorrelationId("t"), mode=BackendMode.NORMAL)
LINK = ProvenanceLink(kind=ProvenanceKind.PASSAGE, ref="doc:1#p1")
GROUNDED = GroundingReport(
    claims_total=1, claims_resolved=1, verdict=GroundingVerdict.FULLY_GROUNDED
)
CONFIDENT = Confidence(raw=0.9, calibrated=0.9)
POINT = OperatingPoint(tau=0.5)


def test_an_answer_needs_provenance() -> None:
    with pytest.raises(InvariantViolation, match="provenance"):
        ReliabilityEnvelope(
            decision=Decision.ANSWER,
            mode=BackendMode.NORMAL,
            trace=TRACE,
            answer="60 kWh",
            provenance=(),
            confidence=CONFIDENT,
            operating_point=POINT,
            grounding=GROUNDED,
        )


def test_an_answer_cannot_carry_an_unresolved_claim() -> None:
    """Invariant 2: the enforced form of evidence-before-generation."""
    unresolved = GroundingReport(
        claims_total=2,
        claims_resolved=1,
        unresolved=(Claim(id=ClaimId("c2"), text="It ships with a 10-year warranty."),),
        verdict=GroundingVerdict.UNRESOLVED_CLAIMS,
    )
    with pytest.raises(InvariantViolation, match="unresolved"):
        ReliabilityEnvelope(
            decision=Decision.ANSWER,
            mode=BackendMode.NORMAL,
            trace=TRACE,
            answer="60 kWh, with a 10-year warranty.",
            provenance=(LINK,),
            confidence=CONFIDENT,
            operating_point=POINT,
            grounding=unresolved,
        )


def test_an_answer_cannot_sit_below_its_own_threshold() -> None:
    with pytest.raises(InvariantViolation, match="below"):
        ReliabilityEnvelope(
            decision=Decision.ANSWER,
            mode=BackendMode.NORMAL,
            trace=TRACE,
            answer="60 kWh",
            provenance=(LINK,),
            confidence=Confidence(raw=0.2, calibrated=0.2),
            operating_point=OperatingPoint(tau=0.7),
            grounding=GROUNDED,
        )


def test_an_answer_must_actually_say_something() -> None:
    with pytest.raises(InvariantViolation, match="answer or a value"):
        ReliabilityEnvelope(
            decision=Decision.ANSWER,
            mode=BackendMode.NORMAL,
            trace=TRACE,
            provenance=(LINK,),
            confidence=CONFIDENT,
            operating_point=POINT,
            grounding=GROUNDED,
        )


def test_an_abstention_must_say_why() -> None:
    """'I don't know' with no reason is not actionable for a practitioner."""
    with pytest.raises(InvariantViolation, match="must say why"):
        ReliabilityEnvelope(decision=Decision.ABSTAIN, mode=BackendMode.NORMAL, trace=TRACE)


def test_a_valid_answer_is_accepted() -> None:
    env = ReliabilityEnvelope.answered(
        mode=BackendMode.CE_RISE,
        trace=TRACE,
        answer="60 kWh",
        provenance=(LINK,),
        confidence=CONFIDENT,
        operating_point=POINT,
        grounding=GROUNDED,
    )
    assert env.answered_ok
    assert env.mode is BackendMode.CE_RISE
    # The operating point travels with the response: an auditor can see the tau
    # that produced this answer without consulting a config file.
    assert env.operating_point.tau == 0.5


def test_an_abstention_names_the_weakest_signal() -> None:
    signals = SignalVector(
        {
            SignalName("retrieval_margin"): 0.8,
            SignalName("snippet_agreement"): 0.1,
        }
    )
    env = ReliabilityEnvelope.abstained(
        mode=BackendMode.NORMAL,
        trace=TRACE,
        reason="below threshold",
        confidence=Confidence(signals=signals, raw=0.45, calibrated=0.45),
    )
    assert env.weak_signal == SignalName("snippet_agreement")


def test_grounding_report_rejects_self_contradiction() -> None:
    with pytest.raises(ValueError, match="must name"):
        GroundingReport(
            claims_total=1, claims_resolved=0, verdict=GroundingVerdict.UNRESOLVED_CLAIMS
        )
    with pytest.raises(ValueError, match="cannot list"):
        GroundingReport(
            claims_total=1,
            claims_resolved=1,
            unresolved=(Claim(id=ClaimId("c"), text="x"),),
            verdict=GroundingVerdict.FULLY_GROUNDED,
        )


def test_provenance_link_needs_a_ref() -> None:
    with pytest.raises(ValueError, match="ref"):
        ProvenanceLink(kind=ProvenanceKind.TRIPLE, ref="")


def test_prose_cannot_use_not_applicable_grounding() -> None:
    with pytest.raises(InvariantViolation, match="fully grounded"):
        ReliabilityEnvelope.answered(
            mode=BackendMode.NORMAL,
            trace=TRACE,
            answer="Unchecked assertion",
            provenance=(LINK,),
            confidence=CONFIDENT,
            operating_point=POINT,
            grounding=GroundingReport.not_applicable(),
        )


@pytest.mark.parametrize(
    "total,resolved,verdict",
    [
        (-1, -1, GroundingVerdict.FULLY_GROUNDED),
        (1, 0, GroundingVerdict.FULLY_GROUNDED),
        (0, 0, GroundingVerdict.FULLY_GROUNDED),
        (1, 1, GroundingVerdict.NOT_APPLICABLE),
    ],
)
def test_grounding_counts_cannot_misrepresent_verdict(total, resolved, verdict) -> None:
    with pytest.raises(ValueError):
        GroundingReport(total, resolved, verdict=verdict)


def test_deterministic_value_can_use_not_applicable_grounding() -> None:
    from ici_core.domain.envelope import QuantifiedValue

    env = ReliabilityEnvelope.answered(
        mode=BackendMode.NORMAL,
        trace=TRACE,
        value=QuantifiedValue(60, "kWh"),
        provenance=(LINK,),
        confidence=CONFIDENT,
        operating_point=POINT,
        grounding=GroundingReport.not_applicable(),
    )
    assert env.answered_ok
