# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""``SymbolicValidator`` over an OWL 2 RL reasoner.

Targeted validity, as the paper puts it: this layer runs where structured facts
and rules exist, and says so honestly when they do not. An empty fact graph
produces an empty result rather than a guess, and ``fired`` is reported either
way — because the published precision figure is conditional on firing, so whether
it fired has to be observable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ici_core.domain.claims import Claim
from ici_core.domain.rules import (
    EntailmentResult,
    FactGraph,
    RuleTrace,
    Triple,
    ValidationReport,
)
from ici_symbolic.config import ReasonerConfig
from ici_symbolic.reasoner import OwlRlReasoner, local_name


@dataclass
class OwlRlValidator:
    """Implements ``SymbolicValidator`` for Normal mode.

    Stateless between calls, deliberately. An earlier draft cached the last
    entailment so ``validate`` could reuse it, and a test immediately caught the
    consequence: validating an empty graph returned conclusions derived for a
    different subject in a previous call. Caching derived state keyed on nothing
    is the same hidden-state bug as the module-level singleton this package was
    written to remove. Entailment over a 4,000-triple graph is milliseconds; the
    cache bought nothing and cost correctness.
    """

    reasoner: OwlRlReasoner

    @classmethod
    def for_domain(cls, domain: str = "battery") -> OwlRlValidator:
        return cls(OwlRlReasoner(ReasonerConfig.for_domain(domain)))

    # -- SymbolicValidator --------------------------------------------------
    def entail(self, graph: FactGraph) -> EntailmentResult:
        """Derive obligations for the subjects named in ``graph``.

        The supplied graph names what we are reasoning *about*; the ontology
        supplies what is *known*. A graph with no subjects has nothing to reason
        about, so the honest answer is an empty result.
        """
        subjects = self._subjects_of(graph)
        if not subjects:
            return EntailmentResult()

        derived: list[Triple] = []
        traces: list[RuleTrace] = []
        fired: list[str] = []

        for firing in self.reasoner.last_outcome.firings:
            relevant = tuple(
                Triple(s, local_name(p), self.reasoner.label_for(o))
                for s, p, o in firing.added
                if local_name(s) in subjects
            )
            if not relevant:
                continue
            fired.append(firing.rule.id)
            derived.extend(relevant)
            traces.extend(
                RuleTrace(
                    rule_id=firing.rule.id,
                    premises=self._premises_for(local_name(conclusion.subject), graph),
                    conclusion=conclusion,
                )
                for conclusion in relevant
            )

        return EntailmentResult(
            derived=tuple(derived),
            traces=tuple(traces),
            rules_fired=tuple(dict.fromkeys(fired)),
        )

    def validate(self, claims: Sequence[Claim], graph: FactGraph) -> ValidationReport:
        """Check claims against what the rules derived.

        Deliberately narrow: this reports a violation only where a rule actually
        speaks to the claim. Flagging everything the rules cannot confirm would
        dilute a guarantee that is only meaningful where it applies.
        """
        entailment = self.entail(graph)
        if not entailment.fired:
            return ValidationReport(checked=0)

        obligations = {t.object.lower() for t in entailment.derived}
        violations: list[str] = []
        for claim in claims:
            text = claim.text.lower()
            missing = [o for o in obligations if o in text and f"not {o}" in text]
            violations.extend(
                f"claim {claim.id} contradicts derived obligation {o!r}" for o in missing
            )

        return ValidationReport(
            checked=len(claims),
            violations=tuple(violations),
            traces=entailment.traces,
        )

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _subjects_of(graph: FactGraph) -> set[str]:
        return {local_name(t.subject) for t in graph.triples}

    @staticmethod
    def _premises_for(subject: str, graph: FactGraph) -> tuple[Triple, ...]:
        """The supplied facts about this subject, which is what the rule read."""
        return tuple(t for t in graph.triples if local_name(t.subject) == subject)

    # -- convenience for the evidence layer ---------------------------------
    def obligations_for(self, product: str) -> tuple[tuple[str, str], ...]:
        """(predicate, label) pairs a product is under. Used to build evidence."""
        pairs = [
            ("requiresCompliance", self.reasoner.label_for(u))
            for u in self.reasoner.requires_compliance(product)
        ]
        pairs += [
            ("requiresStep", self.reasoner.label_for(u))
            for u in self.reasoner.requires_steps(product)
        ]
        return tuple(pairs)

    def fires_for(self, product: str) -> bool:
        """Whether the symbolic layer has anything to say about this product."""
        return bool(
            self.reasoner.requires_compliance(product) or self.reasoner.requires_steps(product)
        )
