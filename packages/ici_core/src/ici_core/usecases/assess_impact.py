# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Environmental impact, through whichever engine the mode bound.

Normal mode works from flat product profiles and CSV factor tables: fast, broad,
shallow. CE-RISE mode solves the supply chain off an RDF graph with the Circular
Footprint Formula. This use case does not know the difference, which is the point.

Two things the envelope's own invariants settled while this was being written, and
both are worth stating rather than working around:

*The result is a ``value``, not an ``answer``.* ``ReliabilityEnvelope`` refuses a
prose ``answer`` that is not fully grounded, because prose is the thing that can
hallucinate. An arithmetic result is not prose; it goes in ``value``, the slot that
exists precisely so a number does not have to be parsed back out of a sentence.

*No operating point applies, so this reports τ = 0.* The selective threshold governs
whether to hazard a composed claim. There is no such judgement here: the engine
either has a product profile or raises, and withholding a computed figure because
its factors were estimated would suppress the very number the caveats exist to
qualify. The stub's ``point`` parameter is therefore gone rather than quietly
ignored — a caller-supplied threshold that does nothing is worse than none.

What *is* reported is a data-quality reading: the contribution-weighted share of the
result resting on measured rather than inferred inputs. It is recorded under its own
signal name so that nothing downstream can mistake it for the retrieval-and-grounding
score ``AnswerQuestion`` produces. The two are not comparable and must never be
averaged.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.confidence import Confidence, OperatingPoint, SignalVector
from ici_core.domain.envelope import Decision, QuantifiedValue, ReliabilityEnvelope
from ici_core.domain.ids import CalibratorId, CorrelationId, SignalName
from ici_core.domain.impact import ImpactRequest, ImpactResult, SubjectRef
from ici_core.domain.trace import Trace, TraceStep
from ici_core.usecases.deps import ProviderBundle

MEASURED_SHARE = SignalName("measured_share")
"""Contribution-weighted share of the result resting on measured inputs."""

DETERMINISTIC = OperatingPoint(tau=0.0)
"""No selective threshold governs arithmetic. Reported, so a reader can see that."""


@dataclass(frozen=True)
class AssessImpact:
    """Assess a subject, and return the result with its derivation attached."""

    bundle: ProviderBundle

    def __call__(
        self,
        subject: SubjectRef,
        req: ImpactRequest,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
    ) -> ReliabilityEnvelope:
        return self.detailed(subject, req, correlation_id=correlation_id)[0]

    def detailed(
        self,
        subject: SubjectRef,
        req: ImpactRequest,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
    ) -> tuple[ReliabilityEnvelope, ImpactResult]:
        """The envelope and the engine result from one assessment.

        Both, from a single call, because a caller usually needs both and running
        the engine twice is how two views of the same question start disagreeing.
        The envelope carries the reliability story — value, provenance, data
        quality; the ``ImpactResult`` carries the domain detail — the per-stage
        breakdown, which is impact-specific and does not belong on an envelope
        shape shared with question answering.
        """
        trace = Trace(correlation_id=correlation_id, mode=self.bundle.mode)

        result = self.bundle.impact.assess(subject, req)
        trace = trace.with_step(
            TraceStep(
                "assess",
                f"{result.total:.6g} {result.unit} across {len(result.contributions)} parts",
            )
        )

        # Fetched unconditionally, not on request: the envelope refuses an ANSWER with
        # no provenance, so a result whose derivation cannot be produced is one this
        # use case is not entitled to return.
        provenance = self.bundle.impact.explain(result, "total")
        trace = trace.with_step(TraceStep("explain", f"{len(provenance.links)} sources"))

        measured = _measured_share(result)
        trace = trace.with_step(TraceStep("data-quality", f"measured share {measured:.3f}"))

        return ReliabilityEnvelope(
            decision=Decision.ANSWER,
            mode=self.bundle.mode,
            trace=trace,
            value=QuantifiedValue(
                amount=result.total,
                unit=result.unit,
                basis=result.functional_unit,
            ),
            provenance=provenance.links,
            confidence=Confidence(
                signals=SignalVector({MEASURED_SHARE: measured}),
                raw=measured,
                calibrated=measured,
                # Named, so the envelope says out loud that nothing was calibrated
                # here. A deterministic engine has no held-out set to calibrate
                # against, and leaving the default would put an uncalibrated number
                # in the field the selective layer reads for answers.
                calibrator_id=CalibratorId("none:data-quality"),
            ),
            operating_point=DETERMINISTIC,
            warnings=result.diagnostics,
        ), result


def _measured_share(result: ImpactResult) -> float:
    """How much of the total rests on measured inputs.

    Weighted by contribution rather than counted per stage: one proxy factor carrying
    80% of the footprint is a different situation from one carrying 2%, and a stage
    count cannot tell them apart.
    """
    total = sum(abs(c.amount) for c in result.contributions)
    if total <= 0:
        # Nothing to weight. Fall back to the engine's own declaration rather than
        # inventing a share, and prefer the pessimistic reading when it says proxy.
        return 0.0 if result.uses_proxy_factors else 1.0
    measured = sum(abs(c.amount) for c in result.contributions if not c.is_proxy)
    return min(1.0, measured / total)


__all__ = ["DETERMINISTIC", "MEASURED_SHARE", "AssessImpact"]
