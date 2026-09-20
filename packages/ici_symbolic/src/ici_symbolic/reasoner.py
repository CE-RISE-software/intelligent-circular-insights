# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""OWL 2 RL reasoning over a DPP ontology, with per-rule attribution.

Two things differ from the service this was ported from, and both matter.

**Rules are applied one at a time, and what each one added is recorded.** The
original ran every CONSTRUCT into the same graph and returned a count of triples
added — so a conclusion could be shown but not attributed. The paper's claim is
that the layer "emits conclusions together with traces", and a trace that cannot
name the rule is not a trace. Running rules individually costs a few more graph
passes over a 4,000-triple graph; that is nothing, and it buys attribution.

**Nothing is read from the environment and nothing is a module-level singleton.**
The original kept a process-wide reasoner keyed by an env var, which makes two
domains in one process impossible.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

from ici_symbolic.config import ReasonerConfig
from ici_symbolic.rules import Rule, rules_for

LOG = logging.getLogger("ici.symbolic")

try:
    from owlrl import DeductiveClosure, OWLRL_Semantics

    OWL_AVAILABLE = True
except ImportError:  # pragma: no cover - owlrl is a declared dependency
    OWL_AVAILABLE = False


@dataclass(frozen=True)
class RuleFiring:
    """What one rule contributed. Empty ``added`` means it did not fire."""

    rule: Rule
    added: tuple[tuple[str, str, str], ...] = ()

    @property
    def fired(self) -> bool:
        return bool(self.added)


@dataclass
class ReasoningOutcome:
    """The result of a full rule pass: totals plus who did what."""

    firings: tuple[RuleFiring, ...] = ()
    triples_before: int = 0
    triples_after: int = 0

    @property
    def added_count(self) -> int:
        return self.triples_after - self.triples_before

    @property
    def rules_fired(self) -> tuple[str, ...]:
        return tuple(f.rule.id for f in self.firings if f.fired)


@dataclass
class OwlRlReasoner:
    """Loads an ontology, closes it under OWL 2 RL, then applies obligation rules."""

    config: ReasonerConfig
    _base: Graph = field(init=False, repr=False)
    graph: Graph = field(init=False, repr=False)
    _disabled: set[str] = field(default_factory=set, init=False, repr=False)
    last_outcome: ReasoningOutcome = field(default_factory=ReasoningOutcome, init=False)

    def __post_init__(self) -> None:
        self.EX = Namespace(self.config.namespace)
        self._base = self._load_and_close()
        self.graph = self._fresh()
        self.apply_rules()

    # -- construction -------------------------------------------------------
    def _load_and_close(self) -> Graph:
        g = Graph()
        g.parse(str(self.config.ontology_path), format="turtle")
        LOG.info("loaded %s (%d triples)", self.config.ontology_path.name, len(g))
        if self.config.run_owl_rl:
            if OWL_AVAILABLE:
                DeductiveClosure(OWLRL_Semantics).expand(g)
                LOG.info("OWL-RL closure complete (%d triples)", len(g))
            else:  # pragma: no cover
                LOG.warning("owlrl unavailable; skipping deductive closure")
        return g

    def _fresh(self) -> Graph:
        """A clean copy of the closed ontology, before any obligation rule runs.

        Rules must always be applied to the same starting point, or disabling one
        and re-running would leave the previous run's conclusions behind — which
        would silently corrupt an ablation.
        """
        g = Graph()
        for triple in self._base:
            g.add(triple)
        g.bind("ex", self.config.namespace)
        g.bind("rdfs", str(RDFS))
        return g

    # -- rules --------------------------------------------------------------
    @property
    def rules(self) -> tuple[Rule, ...]:
        return rules_for(self.config.domain)

    def apply_rules(self) -> ReasoningOutcome:
        """Run every enabled rule, recording what each one contributed."""
        self.graph = self._fresh()
        before = len(self.graph)
        firings: list[RuleFiring] = []

        for rule in self.rules:
            if rule.id in self._disabled:
                continue
            query = prepareQuery(rule.sparql(self.config.namespace))
            added: list[tuple[str, str, str]] = []
            for triple in self.graph.query(query):
                if triple not in self.graph:
                    added.append(tuple(str(term) for term in triple))  # type: ignore[arg-type]
                self.graph.add(triple)  # type: ignore[arg-type]
            firings.append(RuleFiring(rule=rule, added=tuple(added)))

        self.last_outcome = ReasoningOutcome(
            firings=tuple(firings),
            triples_before=before,
            triples_after=len(self.graph),
        )
        LOG.info(
            "rules added %d triples (total %d); fired: %s",
            self.last_outcome.added_count,
            len(self.graph),
            ", ".join(self.last_outcome.rules_fired) or "none",
        )
        return self.last_outcome

    def disable_rules(self, rule_ids: list[str]) -> ReasoningOutcome:
        """Turn rules off and re-derive. Used for ablations, not in production."""
        self._disabled = set(rule_ids or [])
        return self.apply_rules()

    def enable_all_rules(self) -> ReasoningOutcome:
        self._disabled.clear()
        return self.apply_rules()

    # -- queries ------------------------------------------------------------
    def requires_compliance(self, product: str) -> list[str]:
        return sorted(
            str(o) for o in self.graph.objects(self.EX[product], self.EX.requiresCompliance)
        )

    def requires_steps(self, product: str) -> list[str]:
        return sorted(str(o) for o in self.graph.objects(self.EX[product], self.EX.requiresStep))

    def list_products(self) -> list[str]:
        return sorted(str(s) for s in self.graph.subjects(RDF.type, self.EX.Product))

    def label_for(self, uri: str) -> str:
        """A human label if the ontology gives one, otherwise the local name."""
        node = URIRef(uri)
        for label in self.graph.objects(node, RDFS.label):
            return str(label)
        return local_name(uri)


def local_name(uri: str) -> str:
    """The readable tail of an IRI: everything after the last # or /."""
    return uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
