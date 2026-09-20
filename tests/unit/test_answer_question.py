"""The inference path, exercised end to end against fakes.

Written in Sprint 0 rather than Sprint 1 because the orchestration is pure policy
over ports — no I/O, no model — so it is testable the moment the ports exist, and
getting it right now is what makes Sprint 1 mostly mechanical.
"""

from __future__ import annotations

from tests.conftest import (
    FakeEvidenceProvider,
    FakeGrounding,
    FakeSubstrateRegistry,
    FakeSymbolic,
)

from ici_core.domain.claims import Claim, GroundingVerdict
from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.envelope import Decision
from ici_core.domain.ids import ClaimId
from ici_core.domain.query import Query, RetrievalBudget
from ici_core.domain.rules import EntailmentResult, FactGraph, RuleTrace, Triple
from ici_core.usecases.answer_question import AnswerQuestion
from ici_core.usecases.deps import ProviderBundle


def test_answers_when_everything_is_in_order(bundle: ProviderBundle, query: Query) -> None:
    env = AnswerQuestion(bundle)(query)
    assert env.decision is Decision.ANSWER
    assert env.provenance, "invariant 1 must hold in the happy path too"
    assert env.mode is bundle.mode
    assert env.trace.step_names() == (
        "recall",
        "retrieve",
        "entail",
        "compose",
        "grounding",
        "confidence",
    )


def test_abstains_with_a_reason_when_there_is_no_evidence(
    bundle: ProviderBundle, query: Query
) -> None:
    empty = ProviderBundle(**{**bundle.__dict__, "evidence": FakeEvidenceProvider([])})
    env = AnswerQuestion(empty)(query)
    assert env.decision is Decision.ABSTAIN
    assert "No evidence" in (env.abstain_reason or "")


def test_abstains_when_a_claim_cannot_be_grounded(bundle: ProviderBundle, query: Query) -> None:
    """The failure this architecture exists to prevent, at the use-case level."""
    ungrounded = ProviderBundle(
        **{
            **bundle.__dict__,
            "grounding": FakeGrounding(
                verdict=GroundingVerdict.UNRESOLVED_CLAIMS,
                unresolved=(Claim(id=ClaimId("c1"), text="It has a 10-year warranty."),),
            ),
        }
    )
    env = AnswerQuestion(ungrounded)(query)
    assert env.decision is Decision.ABSTAIN
    assert "could not be traced" in (env.abstain_reason or "")
    assert "10-year warranty" in (env.abstain_reason or "")


def test_abstains_below_threshold_and_names_the_weak_signal(
    bundle: ProviderBundle, query: Query
) -> None:
    env = AnswerQuestion(bundle)(query, point=OperatingPoint(tau=0.99))
    assert env.decision is Decision.ABSTAIN
    assert "below the operating threshold" in (env.abstain_reason or "")
    assert env.weak_signal is not None


def test_symbolic_traces_become_provenance(bundle: ProviderBundle, query: Query) -> None:
    conclusion = Triple("cell-1", "requiresCompliance", "IEC-62133")
    fired = ProviderBundle(
        **{
            **bundle.__dict__,
            "substrates": FakeSubstrateRegistry(
                graph=FactGraph((Triple("p1", "hasComponent", "cell-1"),))
            ),
            "symbolic": FakeSymbolic(
                EntailmentResult(
                    derived=(conclusion,),
                    traces=(RuleTrace("obligation-1", (), conclusion),),
                    rules_fired=("obligation-1",),
                )
            ),
        }
    )
    env = AnswerQuestion(fired)(query)
    assert env.decision is Decision.ANSWER
    rule_links = [p for p in env.provenance if p.kind.value == "rule"]
    assert rule_links and rule_links[0].ref == "obligation-1"


def test_symbolic_is_skipped_without_a_product_scope(bundle: ProviderBundle) -> None:
    """Targeted validity: don't claim a guarantee where there are no facts to check."""
    env = AnswerQuestion(bundle)(Query(text="what is a DPP?"))
    entail = [s for s in env.trace.steps if s.name == "entail"]
    assert entail and "skipped" in entail[0].detail


def test_the_budget_is_respected(bundle: ProviderBundle, query: Query) -> None:
    env = AnswerQuestion(bundle)(query, budget=RetrievalBudget(top_k_documents=1))
    passages = [e for e in env.evidence if e.kind.value == "passage"]
    assert len(passages) <= 1


def test_derived_only_evidence_reaches_composition(bundle: ProviderBundle, query: Query) -> None:
    from dataclasses import replace

    from ici_core.domain.evidence import EvidenceKind

    conclusion = Triple("bat-60", "requiresCompliance", "IEC-62133")
    fired = replace(
        bundle,
        evidence=FakeEvidenceProvider([]),
        substrates=FakeSubstrateRegistry(graph=FactGraph((Triple("bat-60", "type", "battery"),))),
        symbolic=FakeSymbolic(
            EntailmentResult(
                derived=(conclusion,),
                traces=(RuleTrace("rule-1", (), conclusion),),
                rules_fired=("rule-1",),
            )
        ),
    )
    env = AnswerQuestion(fired)(query, point=OperatingPoint(tau=0))
    assert env.decision is Decision.ANSWER
    assert any(
        e.kind is EvidenceKind.DERIVED_TRIPLE and e.ref == "rule:rule-1" for e in env.evidence
    )


def test_untraced_symbolic_conclusion_is_not_answer_evidence(
    bundle: ProviderBundle, query: Query
) -> None:
    from dataclasses import replace

    graph = FactGraph((Triple("bat-60", "type", "battery"),))
    fired = replace(
        bundle,
        evidence=FakeEvidenceProvider([]),
        substrates=FakeSubstrateRegistry(graph=graph),
        symbolic=FakeSymbolic(EntailmentResult(derived=graph.triples)),
    )
    assert AnswerQuestion(fired)(query).decision is Decision.ABSTAIN
