"""CE-RISE mode: the PEFDPP graph as an impact engine and a fact substrate.

Where Normal mode reads a flat profile and multiplies by a factor table, this
solves a product system off an RDF graph and can show the triple behind any number.
That difference is the point of having two backends, and it is why both implement
the same ports: a caller asks the same question and chooses how much rigour it wants.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ici_core.domain.envelope import ProvenanceKind, ProvenanceLink
from ici_core.domain.errors import CapabilityError
from ici_core.domain.ids import SubstrateId
from ici_core.domain.impact import (
    ImpactContribution,
    ImpactRequest,
    ImpactResult,
    Provenance,
    SubjectRef,
)
from ici_core.domain.rules import FactGraph, Triple
from ici_core.domain.substrate import CoverageReport, Substrate, SubstrateCoverage
from ici_substrates.paths import PEFDPP_FACTORS_ROOT, PEFDPP_ONTOLOGY_ROOT
from ici_substrates.pefdpp.graph import PefdppGraphService
from ici_substrates.pefdpp.lca import PefdppLcaService
from ici_substrates.pefdpp.questions import (
    CompetencyQuestion,
    CoverageSummary,
    QuestionResult,
    load_questions,
)
from ici_substrates.pefdpp.sparql import check as check_sparql
from ici_substrates.pefdpp.sparql import clamp_limit

PEFDPP_SUBSTRATE = SubstrateId("pefdpp")
NAMESPACE = "https://w3id.org/mintjesba/pefdpp/"


def build_services(
    ontology_root: Path | None = None, factors_root: Path | None = None
) -> tuple[PefdppGraphService, PefdppLcaService]:
    graph = PefdppGraphService(ontology_root or PEFDPP_ONTOLOGY_ROOT)
    lca = PefdppLcaService(graph_service=graph, factors_root=factors_root or PEFDPP_FACTORS_ROOT)
    return graph, lca


@dataclass
class PefdppImpactEngine:
    """Implements ``ImpactEngine`` over the WP3 graph."""

    graph: PefdppGraphService
    lca: PefdppLcaService

    @classmethod
    def build(cls, **kwargs: Path | None) -> PefdppImpactEngine:
        graph, lca = build_services(**kwargs)
        return cls(graph=graph, lca=lca)

    def assess(self, subject: SubjectRef, req: ImpactRequest) -> ImpactResult:
        studies = self.graph.studies()
        if subject.id and subject.id not in studies and subject.kind != "product":
            raise CapabilityError(
                capability=f"PEF study {subject.id!r}",
                mode="ce-rise",
                reason=f"the mounted graph carries {studies}",
            )

        result = self.lca.calculate(scenario=dict(req.scenario) if req.scenario else None)
        headline = result["headline"]
        total = float(headline["climate_change_per_fu"])

        contributions = tuple(
            ImpactContribution(
                label=str(stage["stage"]),
                amount=float(stage["climate_change"]),
                unit=str(headline["climate_change_unit"]),
                share=float(stage.get("share_pct", 0.0)) / 100.0,
                # Background flows use a documented proxy pack, not licensed data.
                # Badging every such number is why the result can be trusted about
                # what it is, rather than mistaken for an EF-compliant declaration.
                is_proxy=True,
            )
            for stage in result.get("by_stage", [])
        )

        band = float(headline.get("uncertainty_band") or 0.0)
        return ImpactResult(
            subject=subject,
            indicator="climate_change",
            total=total,
            unit=str(headline["climate_change_unit"]),
            functional_unit=str(headline.get("fu_label", "")),
            contributions=contributions,
            uncertainty=(total - band, total + band) if band else None,
            data_quality=float(result["data_quality"].get("weighted_dqr") or 0.0),
            diagnostics=tuple(
                f"{d.get('code')}: {d.get('message')}" for d in result.get("diagnostics", [])
            ),
            uses_proxy_factors=True,
        )

    def explain(self, result: ImpactResult, target: str) -> Provenance:
        """The derivation of one number, down to the triple it came from.

        This is what a graph buys over a factor table: ``target`` is a flow IRI, and
        what comes back names the file the triple lives in.
        """
        calculated = self.lca.calculate()
        try:
            detail = self.lca.explain(calculated, target)
        except Exception as exc:
            raise CapabilityError(
                capability=f"explain {target!r}",
                mode="ce-rise",
                reason=f"{type(exc).__name__}: {exc}",
            ) from exc

        links = [
            ProvenanceLink(
                kind=ProvenanceKind.TRIPLE,
                ref=str(triple.get("subject", "")),
                source_file=detail.get("source_file"),
                excerpt=f"{triple.get('predicate')} {triple.get('object')}"[:200],
            )
            for triple in detail.get("triples", [])
        ]
        return Provenance(
            target=target,
            links=tuple(links),
            arithmetic=str(detail.get("arithmetic") or ""),
            scaling_chain=tuple(str(s) for s in detail.get("scaling_chain", [])),
        )


@dataclass
class PefdppSubstrateRegistry:
    """Implements ``SubstrateRegistry`` with a graph that carries real facts.

    Unlike the Normal-mode catalogue, ``facts_for`` here returns triples, so the
    symbolic layer has something to reason over and the coverage report measures
    something real.

    It also carries the LCA engine. That is deliberate: mounting this substrate must
    *add* the graph-solved assessment without displacing the fast CSV path, because
    the two running side by side is the demonstration — the same workbench at two
    levels of rigour, with a visible upgrade path between them. An earlier draft
    swapped the impact engine instead, and the Carbon window promptly stopped
    working for the five products the graph has never heard of.
    """

    graph: PefdppGraphService
    lca: PefdppLcaService | None = None
    questions: tuple[CompetencyQuestion, ...] = field(default_factory=load_questions)
    _seen: int = field(default=0, init=False)
    _fired: int = field(default=0, init=False)

    def mounted(self) -> Sequence[Substrate]:
        return [
            Substrate(
                id=PEFDPP_SUBSTRATE,
                title="PEFDPP — PEF-compliant LCA in a Digital Product Passport",
                kind="graph",
                source=NAMESPACE,
                subjects=tuple(self.graph.activities),
                queryable=True,
            )
        ]

    def facts_for(self, subject: SubjectRef) -> FactGraph:
        self._seen += 1
        activity = self.graph.activities.get(subject.id)
        if activity is None:
            return FactGraph()
        self._fired += 1
        record = activity.as_dict()
        triples = [Triple(subject.id, "type", "Activity")]
        triples += [
            Triple(subject.id, key, str(value))
            for key, value in record.items()
            if isinstance(value, (str, int, float)) and value not in (None, "")
        ]
        return FactGraph(tuple(triples))

    def coverage_report(self) -> CoverageReport:
        return CoverageReport(
            per_substrate=(
                SubstrateCoverage(
                    substrate=PEFDPP_SUBSTRATE,
                    questions_seen=self._seen,
                    questions_fired=self._fired,
                ),
            )
        )

    # -- competency questions ------------------------------------------------
    def run_question(self, question_id: str) -> QuestionResult:
        matches = [q for q in self.questions if q.id == question_id]
        if not matches:
            raise CapabilityError(
                capability=f"competency question {question_id!r}",
                mode="ce-rise",
                reason=f"known ids: {[q.id for q in self.questions]}",
            )
        return self._run(matches[0])

    def run_all_questions(self) -> tuple[QuestionResult, ...]:
        return tuple(self._run(q) for q in self.questions)

    def coverage_summary(self) -> CoverageSummary:
        results = self.run_all_questions()
        return CoverageSummary(live=len(results), answered=sum(1 for r in results if r.answered))

    def _run(self, question: CompetencyQuestion) -> QuestionResult:
        try:
            check_sparql(question.sparql)
            payload = self.graph.query(question.sparql, limit=clamp_limit(None))
        except Exception as exc:
            return QuestionResult(question=question, rows=(), error=f"{type(exc).__name__}: {exc}")
        rows = tuple(dict(row) for row in payload.get("rows", []))
        return QuestionResult(question=question, rows=rows)

    # -- the deep assessment path --------------------------------------------
    @property
    def impact(self) -> PefdppImpactEngine:
        if self.lca is None:
            raise CapabilityError(
                capability="PEF assessment",
                mode="ce-rise",
                reason="this registry was mounted without an LCA engine",
            )
        return PefdppImpactEngine(graph=self.graph, lca=self.lca)

    # -- guarded query -------------------------------------------------------
    def query(self, sparql: str, limit: int | None = None) -> dict[str, Any]:
        check_sparql(sparql)
        return self.graph.query(sparql, limit=clamp_limit(limit))
