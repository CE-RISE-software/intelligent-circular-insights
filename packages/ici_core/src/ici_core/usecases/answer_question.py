# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The inference path: evidence, symbolic validation, composition, decision.

This is the published four-stage architecture with one addition — the grounding
verifier between composition and the confidence step. The orchestration lives here
rather than in an adapter because it is pure policy over ports: no I/O, no model,
no mode. That makes it the thing worth getting right, and the thing that is
testable with plain fakes.

The shape is deliberately linear and boring. Every early return is an abstention
with a reason, because the alternative — falling through with a thinner answer —
is exactly the failure this architecture exists to prevent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ici_core.domain.claims import GroundingReport, GroundingVerdict
from ici_core.domain.confidence import Confidence, OperatingPoint
from ici_core.domain.envelope import (
    Decision,
    ProvenanceKind,
    ProvenanceLink,
    ReliabilityEnvelope,
)
from ici_core.domain.errors import GenerationError
from ici_core.domain.evidence import ContextPack, Evidence, EvidenceKind
from ici_core.domain.ids import EvidenceId
from ici_core.domain.query import Query, RetrievalBudget
from ici_core.domain.rules import EntailmentResult, FactGraph
from ici_core.domain.trace import Trace, TraceStep
from ici_core.usecases.deps import ProviderBundle


@dataclass(frozen=True)
class AnswerQuestion:
    """Answer a question about a product, or decline and say why."""

    bundle: ProviderBundle

    def __call__(
        self,
        query: Query,
        *,
        budget: RetrievalBudget | None = None,
        point: OperatingPoint | None = None,
    ) -> ReliabilityEnvelope:
        budget = budget or RetrievalBudget()
        point = point or OperatingPoint()
        trace = Trace(correlation_id=query.correlation_id, mode=self.bundle.mode)

        # -- 1. evidence acquisition ---------------------------------------
        pack, trace = self._gather(query, budget, trace)

        # -- 2. mounted facts ----------------------------------------------
        # What the substrates already assert about this subject, offered to the
        # composer directly. Without this the graph was fetched, reasoned over and
        # then thrown away unless a rule happened to fire on it, so mounting a richer
        # substrate changed what could be *derived* but not what could be *read*.
        graph, trace = self._facts(query, trace)
        pack = pack.merge(_substrate_evidence(graph, budget, taken=pack.ids, query=query))

        # -- 3. targeted symbolic validation -------------------------------
        # A derived conclusion can itself be the only available answer evidence.
        entailment, trace = self._entail(graph, trace)
        if entailment is not None:
            derived: list[Evidence] = []
            for index, triple in enumerate(entailment.derived):
                rules = [t.rule_id for t in entailment.traces if t.conclusion == triple]
                if not rules:
                    continue  # A conclusion without its rule trace is not auditable.
                candidate = f"derived:{index}"
                while EvidenceId(candidate) in pack.ids:
                    candidate = f"derived:{candidate}"
                derived.append(
                    Evidence(
                        id=EvidenceId(candidate),
                        kind=EvidenceKind.DERIVED_TRIPLE,
                        text=f"{triple.subject} {triple.predicate} {triple.object}",
                        ref=f"rule:{rules[0]}",
                        metadata={"rules": rules},
                    )
                )
            pack = pack.merge(ContextPack(tuple(derived)))
        if not pack:
            return ReliabilityEnvelope.abstained(
                mode=self.bundle.mode,
                trace=trace,
                reason="No evidence was found for this question.",
                operating_point=point,
            )

        # -- 4. composition -------------------------------------------------
        try:
            answer = self.bundle.llm.compose(query.text, pack)
        except GenerationError as exc:
            return ReliabilityEnvelope.abstained(
                mode=self.bundle.mode,
                trace=trace.with_step(TraceStep("compose", type(exc).__name__)),
                reason=f"The model could not supply a complete answer: {exc}",
                operating_point=point,
                evidence=pack.items,
            )
        trace = trace.with_step(TraceStep("compose", f"{len(answer)} chars"))

        # -- 5. grounding ----------------------------------------------------
        grounding = self.bundle.grounding.verify(answer, pack)
        trace = trace.with_step(
            TraceStep("grounding", f"{grounding.claims_resolved}/{grounding.claims_total}")
        )
        if grounding.blocks_answering:
            unresolved = ", ".join(c.text[:60] for c in grounding.unresolved[:3])
            return ReliabilityEnvelope.abstained(
                mode=self.bundle.mode,
                trace=trace,
                reason=(
                    "The drafted answer contained claims that could not be traced to "
                    f"the gathered evidence: {unresolved}"
                ),
                evidence=pack.items,
                grounding=grounding,
                operating_point=point,
            )

        # -- 6. confidence and the selective decision ------------------------
        signals = self.bundle.signals.emit(query, pack, entailment)
        raw = _mean(tuple(signals.values.values()))
        confidence = Confidence(
            signals=signals,
            raw=raw,
            calibrated=self.bundle.calibrator.calibrate(signals, raw),
            calibrator_id=self.bundle.calibrator.id,
        )
        trace = trace.with_step(
            TraceStep("confidence", f"raw={raw:.3f} cal={confidence.calibrated:.3f}")
        )

        if self.bundle.selective.decide(confidence, point) is Decision.ABSTAIN:
            weak = signals.weakest()
            return ReliabilityEnvelope.abstained(
                mode=self.bundle.mode,
                trace=trace,
                reason=(
                    f"Confidence {confidence.calibrated:.2f} is below the operating "
                    f"threshold {point.tau:.2f}"
                    + (f"; the weakest signal was {weak}." if weak else ".")
                ),
                confidence=confidence,
                operating_point=point,
                evidence=pack.items,
                grounding=grounding,
            )

        return ReliabilityEnvelope.answered(
            mode=self.bundle.mode,
            trace=trace,
            answer=answer,
            evidence=pack.items,
            provenance=_provenance_for(pack, entailment),
            confidence=confidence,
            operating_point=point,
            grounding=grounding,
        )

    # -- stages -------------------------------------------------------------
    def _gather(
        self, query: Query, budget: RetrievalBudget, trace: Trace
    ) -> tuple[ContextPack, Trace]:
        """Memory first, then retrieval, deduplicated into one pack.

        Memory goes first because a validated fact about *this* product beats a
        passage that merely mentions it, and because recall is cheap.
        """
        items: list[Evidence] = []

        facts = self.bundle.memory.recall(query.scope, query)
        for i, fact in enumerate(facts[: budget.top_k_memory]):
            items.append(
                Evidence(
                    id=EvidenceId(f"mem:{i}"),
                    kind=EvidenceKind.FACT,
                    text=f"{fact.subject} {fact.predicate} {fact.value}",
                    ref=fact.provenance_ref,
                )
            )
        trace = trace.with_step(TraceStep("recall", f"{len(facts)} facts"))

        retrieved = self.bundle.evidence.retrieve(query, budget)
        items.extend(retrieved[: budget.top_k_documents])
        trace = trace.with_step(TraceStep("retrieve", f"{len(retrieved)} passages"))

        return _dedupe(items), trace

    def _facts(self, query: Query, trace: Trace) -> tuple[FactGraph, Trace]:
        """Everything the mounted substrates assert about the subject.

        Fetched once and used twice — as evidence and as the input to the symbolic
        layer — because two fetches could disagree, and an answer grounded in triples
        the reasoner did not see would be unauditable.
        """
        if not query.scope.is_product_scoped:
            return FactGraph(), trace.with_step(TraceStep("facts", "skipped: no product scope"))

        from ici_core.domain.impact import SubjectRef

        graph = self.bundle.substrates.facts_for(SubjectRef(id=str(query.scope.product_id)))
        return graph, trace.with_step(TraceStep("facts", f"{len(graph.triples)} triples"))

    def _entail(self, graph: FactGraph, trace: Trace) -> tuple[EntailmentResult | None, Trace]:
        """Run the symbolic layer only where there are facts to reason over.

        'Targeted validity': applying it everywhere would dilute a guarantee that
        is only meaningful where structured facts and rules actually exist.
        """
        if not graph:
            return None, trace.with_step(TraceStep("entail", "skipped: empty fact graph"))

        result = self.bundle.symbolic.entail(graph)
        return result, trace.with_step(
            TraceStep("entail", f"{len(result.derived)} derived, fired={result.fired}")
        )


def _substrate_evidence(
    graph: FactGraph,
    budget: RetrievalBudget,
    *,
    taken: frozenset[EvidenceId],
    query: Query | None = None,
) -> ContextPack:
    """Mounted triples as citable evidence, bounded by the budget.

    Kinded ``SUBSTRATE_ROW`` rather than ``FACT``: a fact is something this system
    validated and remembered, whereas this is what a mounted source asserts. The
    distinction survives into provenance, so a reader can tell an assertion the
    consortium's graph makes from one this deployment has confirmed.

    ``taken`` is the ids already in the pack, so a collision widens the id rather
    than raising on a duplicate — ``ContextPack`` rejects duplicates by design.
    """
    # A subject can have dozens of assertions. Taking the first N makes the result
    # depend on serialisation order: a requested fact may exist in the graph but be
    # invisible merely because it was emitted later. Rank predicates and values
    # against the question, keeping the original order as the deterministic tie
    # breaker. The subject is deliberately excluded because every row in a
    # product-scoped graph normally has the same subject and would therefore make
    # every score identical.
    indexed = list(enumerate(graph.triples))
    if query is not None:
        terms = _lexical_terms(query.text)
        indexed.sort(
            key=lambda row: (
                -_triple_relevance(row[1].predicate, row[1].object, terms),
                row[0],
            )
        )

    items: list[Evidence] = []
    used = set(taken)
    for index, triple in indexed[: budget.top_k_facts]:
        # Predicate-based ids are stable when the source adds or reorders other
        # triples, and give the composer an opaque-but-meaningful string it can
        # copy verbatim. Numeric row ids prompted small models to emit shortened
        # citations such as ``[12]``, which the safety guard correctly rejected.
        component = re.sub(r"[^A-Za-z0-9_.:/-]+", "-", triple.predicate).strip("-")
        base = f"substrate:{component or 'row'}"
        candidate = base
        if EvidenceId(candidate) in used:
            candidate = f"{base}:{index}"
        while EvidenceId(candidate) in used:
            candidate = f"{candidate}:{index}"
        used.add(EvidenceId(candidate))
        items.append(
            Evidence(
                id=EvidenceId(candidate),
                kind=EvidenceKind.SUBSTRATE_ROW,
                text=f"{triple.subject} {triple.predicate} {triple.object}",
                ref=f"substrate:{triple.subject}",
            )
        )
    return ContextPack(tuple(items))


_WORD = re.compile(r"[A-Za-z0-9]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "does",
        "for",
        "from",
        "how",
        "is",
        "of",
        "the",
        "this",
        "to",
        "what",
        "which",
        "who",
        "with",
    }
)


def _lexical_terms(value: str) -> frozenset[str]:
    """Small deterministic term set for selecting graph rows, not full-text search."""
    separated = _CAMEL_BOUNDARY.sub(" ", value).replace("_", " ").replace(".", " ")
    terms: set[str] = set()
    for match in _WORD.finditer(separated.lower()):
        token = match.group(0)
        if token in _STOP_WORDS or len(token) < 2:
            continue
        terms.add(token)
        # Enough morphology for graph predicates such as commissioner to match a
        # natural question phrased as "who commissioned ...". Keep the original
        # token too so this cannot reduce exact-match recall.
        for suffix in ("ing", "ed", "er", "es", "s"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 4:
                terms.add(token[: -len(suffix)])
                break
    return frozenset(terms)


def _triple_relevance(predicate: str, value: str, query_terms: frozenset[str]) -> int:
    predicate_overlap = len(query_terms & _lexical_terms(predicate))
    value_overlap = len(query_terms & _lexical_terms(value))
    # Predicate matches carry more intent than words occurring in a long value.
    return 4 * predicate_overlap + value_overlap


def _dedupe(items: list[Evidence]) -> ContextPack:
    by_id: dict[EvidenceId, Evidence] = {}
    for item in items:
        by_id.setdefault(item.id, item)
    return ContextPack(tuple(by_id.values()))


def _mean(values: tuple[float, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


def _provenance_for(
    pack: ContextPack, entailment: EntailmentResult | None
) -> tuple[ProvenanceLink, ...]:
    """Every piece of evidence becomes a link, plus one per fired rule.

    Built from the pack rather than from the answer text, so provenance cannot be
    empty while evidence exists — which keeps invariant 1 satisfiable by
    construction rather than by an adapter remembering.
    """
    links = [
        ProvenanceLink(
            kind=_KIND_MAP.get(item.kind, ProvenanceKind.PASSAGE),
            ref=item.ref,
            source_file=item.source_file,
            excerpt=item.text[:200] or None,
        )
        for item in pack.items
    ]
    if entailment is not None:
        links.extend(
            ProvenanceLink(kind=ProvenanceKind.RULE, ref=t.rule_id, excerpt=str(t.conclusion))
            for t in entailment.traces
        )
    return tuple(links)


_KIND_MAP = {
    EvidenceKind.PASSAGE: ProvenanceKind.PASSAGE,
    EvidenceKind.FACT: ProvenanceKind.FACT,
    EvidenceKind.DERIVED_TRIPLE: ProvenanceKind.TRIPLE,
    EvidenceKind.SUBSTRATE_ROW: ProvenanceKind.TRIPLE,
    EvidenceKind.CALC_STEP: ProvenanceKind.CALC_STEP,
}

__all__ = ["AnswerQuestion", "GroundingReport", "GroundingVerdict"]
