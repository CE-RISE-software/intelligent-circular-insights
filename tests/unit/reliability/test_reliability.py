"""Signals, calibration and the selective decision."""

from __future__ import annotations

import pytest

from ici_core.domain.confidence import (
    GENERATION_PROBABILITY,
    RETRIEVAL_MARGIN,
    SNIPPET_AGREEMENT,
    SYMBOLIC_FIRED,
    Confidence,
    OperatingPoint,
    SignalVector,
)
from ici_core.domain.envelope import Decision
from ici_core.domain.evidence import ContextPack, Evidence, EvidenceKind
from ici_core.domain.ids import EvidenceId
from ici_core.domain.query import Query
from ici_core.domain.rules import EntailmentResult
from ici_policy import ABSTAIN, ANSWER, RETRIEVE, HeuristicRouter
from ici_reliability import (
    EvidenceSignals,
    IdentityCalibrator,
    IsotonicCalibrator,
    ThresholdSelectivePolicy,
)


def pack(*scores: float) -> ContextPack:
    return ContextPack(
        tuple(
            Evidence(
                id=EvidenceId(f"e{i}"),
                kind=EvidenceKind.PASSAGE,
                text=f"passage {i} about battery capacity",
                ref=f"doc:{i}",
                score=s,
            )
            for i, s in enumerate(scores)
        )
    )


QUERY = Query(text="what is the capacity")


class TestSignals:
    def test_every_declared_signal_is_emitted(self) -> None:
        signals = EvidenceSignals()
        emitted = signals.emit(QUERY, pack(1.0, 0.5), None)
        assert set(signals.names()) <= set(emitted.values)

    def test_empty_pack_gives_zero_margin(self) -> None:
        assert EvidenceSignals().emit(QUERY, ContextPack(), None).get(RETRIEVAL_MARGIN) == 0.0

    def test_a_clear_winner_scores_a_wide_margin(self) -> None:
        wide = EvidenceSignals().emit(QUERY, pack(1.0, 0.1), None).get(RETRIEVAL_MARGIN)
        narrow = EvidenceSignals().emit(QUERY, pack(1.0, 0.99), None).get(RETRIEVAL_MARGIN)
        assert wide > narrow

    def test_a_single_passage_cannot_agree_with_itself(self) -> None:
        # Claiming certainty from one source is precisely the failure mode here,
        # so one item is neutral rather than perfect agreement.
        assert EvidenceSignals().emit(QUERY, pack(1.0), None).get(SNIPPET_AGREEMENT) == 0.5

    def test_symbolic_firing_is_observable(self) -> None:
        # The published precision figure is conditional on firing, so whether it
        # fired has to be visible in the vector.
        fired = EntailmentResult(rules_fired=("r1",))
        assert EvidenceSignals().emit(QUERY, pack(1.0), fired).get(SYMBOLIC_FIRED) == 1.0
        assert EvidenceSignals().emit(QUERY, pack(1.0), None).get(SYMBOLIC_FIRED) == 0.0

    def test_generation_probability_defaults_to_neutral(self) -> None:
        assert EvidenceSignals().emit(QUERY, pack(1.0), None).get(GENERATION_PROBABILITY) == 0.5


class TestCalibration:
    @pytest.mark.parametrize("calibrator", [IdentityCalibrator(), IsotonicCalibrator()])
    @pytest.mark.parametrize("raw", [-5.0, 0.0, 0.5, 1.0, 5.0])
    def test_output_is_always_a_probability(self, calibrator, raw) -> None:
        assert 0.0 <= calibrator.calibrate(SignalVector(), raw) <= 1.0

    def test_isotonic_is_monotone_after_fitting(self) -> None:
        cal = IsotonicCalibrator()
        samples = [SignalVector({RETRIEVAL_MARGIN: i / 20}) for i in range(21)]
        cal.fit(samples, [i > 10 for i in range(21)])
        outputs = [cal.calibrate(SignalVector(), i / 20) for i in range(21)]
        assert outputs == sorted(outputs), "a calibrator must never reorder answers"

    def test_an_unfitted_calibrator_says_so_in_its_id(self) -> None:
        # A response names its calibrator. "isotonic" when nothing was fitted
        # would overstate what happened.
        assert "unfitted" in IsotonicCalibrator().id

    def test_fitting_on_no_data_is_a_no_op_not_a_crash(self) -> None:
        cal = IsotonicCalibrator()
        cal.fit([], [])
        assert cal.calibrate(SignalVector(), 0.5) == 0.5


class TestSelectivePolicy:
    def test_answers_at_or_above_tau_and_abstains_below(self) -> None:
        policy = ThresholdSelectivePolicy()
        point = OperatingPoint(tau=0.5)
        assert policy.decide(Confidence(calibrated=0.5), point) is Decision.ANSWER
        assert policy.decide(Confidence(calibrated=0.49), point) is Decision.ABSTAIN

    def test_higher_coverage_means_a_lower_threshold(self) -> None:
        policy = ThresholdSelectivePolicy()
        assert policy.threshold_for(0.9) < policy.threshold_for(0.5)


class TestRouter:
    def test_chosen_action_is_always_in_the_declared_set(self) -> None:
        router = HeuristicRouter()
        for margin in (0.0, 0.5, 1.0):
            action = router.act(SignalVector({RETRIEVAL_MARGIN: margin}), 0)
            assert action in router.actions()

    def test_a_fired_rule_is_enough_to_answer(self) -> None:
        router = HeuristicRouter()
        signals = SignalVector({SYMBOLIC_FIRED: 1.0, RETRIEVAL_MARGIN: 0.0})
        assert router.act(signals, 0) == ANSWER

    def test_thin_evidence_retrieves_once_then_gives_up(self) -> None:
        router = HeuristicRouter()
        thin = SignalVector({RETRIEVAL_MARGIN: 0.0})
        assert router.act(thin, 0) == RETRIEVE
        assert router.act(thin, 1) == ABSTAIN

    def test_an_exhausted_budget_abstains_rather_than_answering(self) -> None:
        # Answering on exhausted evidence is how a system produces confident
        # nonsense, so the budget ends in abstention, not a best guess.
        router = HeuristicRouter(max_steps=3)
        strong = SignalVector({SYMBOLIC_FIRED: 1.0, RETRIEVAL_MARGIN: 1.0})
        assert router.act(strong, 3) == ABSTAIN
