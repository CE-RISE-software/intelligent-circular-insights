"""Carbon and the CE-RISE catalogue, checked against the oracle."""

from __future__ import annotations

import json
import pathlib

import pytest

from ici_core.domain.errors import CapabilityError
from ici_core.domain.ids import DppId, ProfileId
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.domain.record import DPPRecord, ViolationKind
from ici_substrates import (
    CeRiseModelRegistry,
    CsvFactorImpactEngine,
    InMemoryRepository,
    JsonSchemaRegistry,
)

ORACLE = pathlib.Path(__file__).resolve().parents[2] / "reference" / "carbon"


@pytest.fixture(scope="module")
def engine() -> CsvFactorImpactEngine:
    return CsvFactorImpactEngine.from_data_root()


class TestCarbonMatchesTheOracle:
    """Captured from the pre-port engine. A refactor that moves these is a bug."""

    @pytest.mark.parametrize(
        ("product", "case"),
        [
            ("apple_iphone15_pro_128gb", "representative_iphone15"),
            ("generic_bev_pack_60kwh", "representative_bev_pack"),
        ],
    )
    def test_total_is_unchanged(self, engine, product, case) -> None:
        expected = json.loads((ORACLE / f"{case}.json").read_text())
        body = expected.get("body", expected)
        result = engine.assess(SubjectRef(id=product), ImpactRequest())
        assert round(result.total, 6) == round(body["total_kg_co2e"], 6)

    def test_stage_contributions_sum_to_the_total(self, engine) -> None:
        result = engine.assess(SubjectRef(id="apple_iphone15_pro_128gb"), ImpactRequest())
        assert round(sum(c.amount for c in result.contributions), 6) == round(result.total, 6)

    def test_uncertainty_band_brackets_the_total(self, engine) -> None:
        result = engine.assess(SubjectRef(id="apple_iphone15_pro_128gb"), ImpactRequest())
        low, high = result.uncertainty
        assert low <= result.total <= high

    def test_a_number_always_carries_a_unit(self, engine) -> None:
        result = engine.assess(SubjectRef(id="fairphone_4"), ImpactRequest())
        assert result.unit == "kg CO2e"
        assert all(c.unit for c in result.contributions)


class TestCarbonBoundaries:
    def test_an_unsupported_indicator_is_a_capability_error_not_a_crash(self, engine) -> None:
        # A mode that cannot serve something says so, with a reason. 422, not 500.
        with pytest.raises(CapabilityError, match=r"EF 3\.1"):
            engine.assess(SubjectRef(id="fairphone_4"), ImpactRequest(indicator="acidification"))

    def test_an_unknown_product_raises_the_same_error_as_before(self, engine) -> None:
        # Frozen behaviour: the pre-port engine raised FileNotFoundError, so a port
        # that swallowed it into an empty result would be a silent change.
        with pytest.raises(FileNotFoundError):
            engine.assess(SubjectRef(id="no_such_product_at_all"), ImpactRequest())

    def test_explain_returns_links_for_every_stage(self, engine) -> None:
        result = engine.assess(SubjectRef(id="fairphone_4"), ImpactRequest())
        prov = engine.explain(result, "total")
        assert prov.links
        assert len(prov.scaling_chain) == len(result.contributions)
        assert all(link.ref for link in prov.links)


class TestCeRiseCatalogue:
    def test_all_seventeen_models_load(self) -> None:
        assert len(CeRiseModelRegistry().models) == 17

    def test_every_model_names_its_upstream_repository(self) -> None:
        # The vendored schemas are CC-BY-NC-4.0 while this code is EUPL-1.2, so
        # attribution is a licence obligation, not a nicety (ADR 0010).
        for model in CeRiseModelRegistry().models:
            assert model.url.startswith("https://codeberg.org/CE-RISE-models/")

    def test_routing_finds_the_material_models_for_a_material_question(self) -> None:
        hits = CeRiseModelRegistry().route("recycled content of this battery")
        assert [m.id for m in hits][:1] == ["material-profile"]

    def test_an_empty_question_routes_nowhere(self) -> None:
        assert CeRiseModelRegistry().route("") == ()

    def test_facts_for_is_honestly_empty(self) -> None:
        # The catalogue describes shapes, not instances. Inventing triples here
        # would let the symbolic layer "fire" on nothing and inflate the very
        # coverage number the registry exists to measure.
        assert len(CeRiseModelRegistry().facts_for(SubjectRef(id="anything"))) == 0

    def test_coverage_is_reportable(self) -> None:
        reg = CeRiseModelRegistry()
        reg.route("recycled content")
        report = reg.coverage_report()
        assert report.per_substrate
        assert report.per_substrate[0].questions_fired == 1


class TestSchemaConformance:
    def test_violations_are_typed_and_located(self) -> None:
        registry = JsonSchemaRegistry()
        report = registry.conform(DPPRecord(dpp_id=DppId("d1")), ProfileId("eu-dpp"))
        assert not report.conforms
        for violation in report.violations:
            assert violation.location.startswith("/")
            assert isinstance(violation.kind, ViolationKind)
            assert violation.message

    def test_missing_required_fields_are_named_as_such(self) -> None:
        report = JsonSchemaRegistry().conform(DPPRecord(dpp_id=DppId("d1")), ProfileId("eu-dpp"))
        assert any(v.kind is ViolationKind.MISSING_REQUIRED for v in report.violations)

    def test_an_unknown_profile_is_reported_not_raised(self) -> None:
        report = JsonSchemaRegistry().conform(
            DPPRecord(dpp_id=DppId("d1")), ProfileId("no-such-profile")
        )
        assert not report.conforms
        assert "no such profile" in report.violations[0].message


def test_repository_round_trips() -> None:
    repo = InMemoryRepository()
    record = DPPRecord(dpp_id=DppId("d1"), payload={"a": 1})
    repo.put(record)
    assert repo.get(DppId("d1")) is record
    assert repo.get(DppId("missing")) is None
    assert list(repo.list_ids()) == [DppId("d1")]
