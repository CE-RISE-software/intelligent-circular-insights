"""The WP3 integration, checked against the figures the paper publishes.

These numbers are the visible output of the PEFDPP work. If a refactor moves one,
that is a regression in the thing a consortium reviewer would actually notice, so
they are pinned here rather than left to a smoke test.
"""

from __future__ import annotations

import pytest

from ici_core.domain.errors import CapabilityError
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_substrates.pefdpp import (
    PefdppImpactEngine,
    PefdppSubstrateRegistry,
    UnsafeQueryError,
    build_services,
    check,
    clamp_limit,
    load_questions,
)

STUDY = SubjectRef(id="BatteryPackPEFStudy", kind="study")


@pytest.fixture(scope="module")
def services():
    return build_services()


@pytest.fixture(scope="module")
def engine(services) -> PefdppImpactEngine:
    graph, lca = services
    return PefdppImpactEngine(graph=graph, lca=lca)


@pytest.fixture(scope="module")
def registry(services) -> PefdppSubstrateRegistry:
    return PefdppSubstrateRegistry(graph=services[0])


class TestTheGraph:
    def test_triple_count_matches_the_paper(self, services) -> None:
        graph, _ = services
        assert len(graph.graph) == 5387

    def test_fifteen_unit_processes(self, services) -> None:
        graph, _ = services
        assert len(graph.activities) == 15

    def test_the_five_actor_datasets_are_present(self, services) -> None:
        # The case study is deliberately split across five actors — that split is
        # the argument for graph-based passports in miniature.
        graph, _ = services
        names = set(graph.datasets)
        for actor in (
            "CellDataset",
            "ModuleDataset",
            "PackDataset",
            "BatteryEoL",
            "BrazingDataset",
        ):
            assert actor in names, f"{actor} missing from the mounted graph"

    def test_the_heavy_flow_list_is_not_loaded_by_default(self, services) -> None:
        # 41 MB, deliberately uncommitted. Loading it on startup would cost every
        # caller ~40s for a lookup almost nobody makes.
        graph, _ = services
        assert not graph._elementary_scheme_loaded


class TestPublishedResults:
    def test_climate_change_per_functional_unit(self, engine) -> None:
        result = engine.assess(STUDY, ImpactRequest())
        assert round(result.total, 4) == 0.0594

    def test_contribution_weighted_dqr(self, engine) -> None:
        result = engine.assess(STUDY, ImpactRequest())
        assert round(result.data_quality, 6) == 1.218988
        assert round(result.data_quality, 2) == 1.22

    def test_stage_shares(self, engine) -> None:
        result = engine.assess(STUDY, ImpactRequest())
        shares = {c.label: round((c.share or 0) * 100) for c in result.contributions}
        assert shares["Manufacturing"] == 85
        assert shares["EndOfLife"] == 11
        assert shares["Distribution"] == 4

    def test_shares_sum_to_one(self, engine) -> None:
        result = engine.assess(STUDY, ImpactRequest())
        assert round(sum(c.share or 0 for c in result.contributions), 3) == 1.0

    def test_every_number_is_badged_as_proxy_backed(self, engine) -> None:
        # This is not an EF-compliant declaration, and the result says so rather
        # than leaving a reader to find the caveat in a footnote.
        result = engine.assess(STUDY, ImpactRequest())
        assert result.uses_proxy_factors is True
        assert all(c.is_proxy for c in result.contributions)

    def test_the_graph_diagnostics_still_fire(self, engine) -> None:
        # Findings the WP3 note calls out: things a PDF would have hidden.
        result = engine.assess(STUDY, ImpactRequest())
        codes = " ".join(result.diagnostics)
        assert "stage_not_populated" in codes


class TestCompetencyQuestions:
    def test_sixteen_are_live(self) -> None:
        assert len(load_questions()) == 16

    def test_all_sixteen_answer(self, registry) -> None:
        results = registry.run_all_questions()
        failed = [r.question.id for r in results if not r.answered]
        assert not failed, f"competency questions returning nothing: {failed}"

    def test_coverage_is_reported_against_the_papers_full_set(self, registry) -> None:
        # 16 of 173 is a starting point stated honestly, not a gap hidden by
        # counting only what works.
        summary = registry.coverage_summary()
        assert summary.live == 16
        assert summary.total_in_paper == 173
        assert 0.09 < summary.share_of_paper < 0.10

    def test_every_question_cites_the_requirement_it_came_from(self) -> None:
        for question in load_questions():
            assert question.pef_requirement, f"{question.id} cites no PEF requirement"
            assert question.why_it_matters

    def test_an_unknown_question_is_a_capability_error(self, registry) -> None:
        with pytest.raises(CapabilityError, match="known ids"):
            registry.run_question("cq-does-not-exist")


class TestSparqlGuard:
    @pytest.mark.parametrize(
        "hostile",
        [
            "DELETE WHERE { ?s ?p ?o }",
            "INSERT DATA { <a> <b> <c> }",
            "DROP GRAPH <g>",
            "CLEAR ALL",
            "LOAD <http://example.com/evil.ttl>",
            "COPY DEFAULT TO <g>",
            "MOVE DEFAULT TO <g>",
            "SELECT * WHERE { SERVICE <http://evil> { ?s ?p ?o } }",
            "",
            "   ",
            "not a query at all",
        ],
    )
    def test_refused(self, hostile: str) -> None:
        with pytest.raises(UnsafeQueryError):
            check(hostile)

    def test_a_legitimate_read_is_allowed(self) -> None:
        check("SELECT ?s WHERE { ?s ?p ?o } LIMIT 5")
        check("ASK { ?s ?p ?o }")
        check("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")

    def test_a_literal_mentioning_an_update_keyword_is_not_refused(self) -> None:
        # Literals are stripped before scanning. A naive substring match would
        # reject this, which is the sort of guard that teaches people to work
        # around it.
        check('SELECT ?s WHERE { ?s ?p "please delete this record" }')

    def test_a_comment_mentioning_a_keyword_is_not_refused(self) -> None:
        check("# we never DELETE here\nSELECT ?s WHERE { ?s ?p ?o }")

    def test_limits_are_clamped(self) -> None:
        assert clamp_limit(None) == 200
        assert clamp_limit(5) == 5
        assert clamp_limit(10_000) == 1000
        assert clamp_limit(-3) == 1

    def test_the_registry_refuses_unsafe_queries_too(self, registry) -> None:
        with pytest.raises(UnsafeQueryError):
            registry.query("DELETE WHERE { ?s ?p ?o }")


class TestSubstrate:
    def test_it_declares_itself_queryable(self, registry) -> None:
        mounted = list(registry.mounted())
        assert mounted[0].queryable is True
        assert mounted[0].kind == "graph"

    def test_facts_for_a_known_activity_returns_triples(self, registry, services) -> None:
        graph, _ = services
        known = next(iter(graph.activities))
        assert len(registry.facts_for(SubjectRef(id=known))) > 0

    def test_facts_for_an_unknown_subject_is_empty(self, registry) -> None:
        assert len(registry.facts_for(SubjectRef(id="no-such-activity"))) == 0

    def test_coverage_counts_only_subjects_it_actually_knew(self, registry, services) -> None:
        graph, _ = services
        fresh = PefdppSubstrateRegistry(graph=graph)
        fresh.facts_for(SubjectRef(id=next(iter(graph.activities))))
        fresh.facts_for(SubjectRef(id="no-such-activity"))
        coverage = fresh.coverage_report().per_substrate[0]
        assert coverage.questions_seen == 2
        assert coverage.questions_fired == 1
        assert coverage.fire_rate == 0.5
