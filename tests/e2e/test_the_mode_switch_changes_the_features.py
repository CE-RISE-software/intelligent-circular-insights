# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""What flipping the backend switch actually does to the five features.

The point of two backends is that QA, Carbon, Validate, Repair and Synthesize run
over CE-RISE data models, schemas and the WP3 ontology when CE-RISE mode is on.
For three sprints they did not: the switch mounted an extra window and changed
nothing any of the five features did.

The cause was a test. An early draft of CE-RISE mode swapped the impact engine
outright, which broke Carbon for the five products the graph has never heard of.
The repair made CE-RISE purely *additive* and pinned it with an assertion that the
two modes "differ in exactly one port" — which removed the breakage by removing the
difference, and then guarded the absence. Every gate passed for three sprints while
the feature the switch existed to change stayed identical.

So this file asserts the difference feature by feature, and asserts the
non-breakage beside it, because those two are what the design has to hold at once.
Each class is one feature; each carries the specific regression it is guarding.
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest
from apps.api.bundles import build_registry
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient
from tests.llm_recording_cases import ROUTE_SEED

from ici_core.domain.evidence import EvidenceKind
from ici_core.domain.ids import CorrelationId, ProductId
from ici_core.domain.modes import BackendMode
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.trace import Trace
from ici_core.usecases.answer_question import AnswerQuestion, _substrate_evidence

NORMAL = {"X-Backend-Mode": "normal"}
CE_RISE = {"X-Backend-Mode": "ce-rise"}

# The study the WP3 graph models, and a product only the factor table models. Named
# here because every assertion below turns on the difference between the two.
STUDY = "BatteryPackPEFStudy"
PRODUCT = "generic_bev_pack_60kwh"


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c


@pytest.fixture(scope="module")
def recorded() -> TestClient:
    """A client replaying the bounded recorder's real responses. Never calls out."""
    settings = Settings(llm_cassette_dir="tests/cassettes/recorded", llm_cassette_mode="replay")
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture(scope="module")
def registry():
    return build_registry((BackendMode.NORMAL, BackendMode.CE_RISE), Settings())


class TestQaSeesTheGraph:
    """Search & Answer, asserted on the evidence pack.

    Not through ``/api/search``: composing an answer needs a model call, and in
    replay a question with no recorded response abstains before the evidence
    matters. The pack is where the mode difference is real, so that is what is
    measured -- and it is measured through the same ``AnswerQuestion`` both modes
    run, not a reimplementation of it.
    """

    @staticmethod
    def _rows(registry, mode: BackendMode, subject: str) -> tuple:
        bundle = registry.for_mode(mode)
        use_case = AnswerQuestion(bundle)
        query = Query(
            text="What does this describe?",
            scope=ProductScope(product_id=ProductId(subject)),
            correlation_id=CorrelationId("test"),
        )
        budget = RetrievalBudget()
        trace = Trace(correlation_id=query.correlation_id, mode=mode)
        pack, trace = use_case._gather(query, budget, trace)
        graph, _ = use_case._facts(query, trace)
        return _substrate_evidence(graph, budget, taken=pack.ids).items

    def test_ce_rise_answers_from_graph_facts_and_normal_has_none(self, registry) -> None:
        normal = self._rows(registry, BackendMode.NORMAL, STUDY)
        ce_rise = self._rows(registry, BackendMode.CE_RISE, STUDY)
        assert normal == ()
        assert ce_rise, "CE-RISE mode must offer the graph's assertions as evidence"
        assert all(e.kind is EvidenceKind.SUBSTRATE_ROW for e in ce_rise)
        assert any(STUDY in e.text for e in ce_rise)

    def test_the_facts_are_bounded_by_the_budget(self, registry) -> None:
        # A mounted substrate is not a licence to put a whole subgraph in a prompt.
        rows = self._rows(registry, BackendMode.CE_RISE, STUDY)
        assert len(rows) <= RetrievalBudget().top_k_facts

    def test_a_product_the_graph_does_not_model_is_unchanged(self, registry) -> None:
        assert self._rows(registry, BackendMode.CE_RISE, PRODUCT) == ()
        assert self._rows(registry, BackendMode.NORMAL, PRODUCT) == ()


class TestCarbonIsSolvedOffTheGraph:
    def test_the_study_is_assessable_only_in_ce_rise_mode(self, client) -> None:
        normal = client.post("/api/carbon/calculate", json={"product_id": STUDY}, headers=NORMAL)
        ce_rise = client.post("/api/carbon/calculate", json={"product_id": STUDY}, headers=CE_RISE)

        # Normal mode says plainly that it cannot, rather than crashing: an
        # unhandled FileNotFoundError here was a 500, and a 500 also strips the
        # mode header on the way out.
        assert normal.status_code == 422
        assert normal.headers["X-Backend-Mode-Used"] == "normal"

        assert ce_rise.status_code == 200
        body = ce_rise.json()
        assert body["unit"] == "kg CO2 eq"
        assert body["total"] == pytest.approx(0.059384, rel=1e-4)

    def test_the_result_names_the_engine_that_produced_it(self, client) -> None:
        """Two engines behind one port, and the caller can always tell which answered.

        Without this a graph-solved figure and a table-multiplied one are
        indistinguishable in the response, and they are not comparable numbers.
        """
        study = client.post(
            "/api/carbon/calculate", json={"product_id": STUDY}, headers=CE_RISE
        ).json()
        product = client.post(
            "/api/carbon/calculate", json={"product_id": PRODUCT}, headers=CE_RISE
        ).json()
        assert study["diagnostics"][0] == "engine: pefdpp-graph"
        assert product["diagnostics"][0] == "engine: csv-factors"

    def test_the_products_the_graph_never_heard_of_still_work(self, client) -> None:
        """The regression that caused all of this, guarded directly.

        Swapping the impact engine broke Carbon for these five. Routing is what lets
        the mode add the study without taking the products away.
        """
        normal = client.post(
            "/api/carbon/calculate", json={"product_id": PRODUCT}, headers=NORMAL
        ).json()
        ce_rise = client.post(
            "/api/carbon/calculate", json={"product_id": PRODUCT}, headers=CE_RISE
        ).json()
        assert normal["total"] == ce_rise["total"]
        assert normal["unit"] == ce_rise["unit"] == "kg CO2e"

    def test_the_two_engines_are_not_interchangeable(self, client) -> None:
        """Why routing, and not substitution.

        The graph solves a product system declared per kilowatt-hour; the factor
        table totals a product over its whole lifecycle. Four orders of magnitude
        apart, and mapping one onto the other to make the switch 'do something'
        would produce a confidently wrong number.
        """
        study = client.post(
            "/api/carbon/calculate", json={"product_id": STUDY}, headers=CE_RISE
        ).json()
        product = client.post(
            "/api/carbon/calculate", json={"product_id": PRODUCT}, headers=CE_RISE
        ).json()
        assert study["functional_unit"] != product["functional_unit"]
        assert study["total"] * 1000 < product["total"]

    def test_the_graph_explains_its_headline_number(self, client) -> None:
        # Every engine behind the port must answer for "total": it is the number
        # the window shows, and the trace step asks for it on every request.
        body = client.post(
            "/api/carbon/calculate",
            json={"product_id": STUDY, "include_trace": True},
            headers=CE_RISE,
        ).json()
        assert body["arithmetic"]
        assert "kg CO2 eq" in body["arithmetic"]
        assert body["provenance"]


class TestValidateChecksTheCeRiseModels:
    PRODUCT_SYSTEM: ClassVar[dict[str, Any]] = {
        "product_system_identifier": "ps-1",
        "product_system_name": "Battery pack product system",
        "activity_references": [{"activity_identifier": "a1"}],
    }
    PASSPORT: ClassVar[dict[str, Any]] = {
        "schema_version": "1.0.0",
        "dpp_id": "urn:dpp:example",
        "product": {"name": "X"},
        "materials": [{"name": "Steel", "share_pct": 100}],
        "compliance": {},
    }

    def test_a_ce_rise_document_is_checked_against_its_own_model(self, client) -> None:
        normal = client.post("/api/validate", json={"dpp": self.PRODUCT_SYSTEM}, headers=NORMAL)
        ce_rise = client.post("/api/validate", json={"dpp": self.PRODUCT_SYSTEM}, headers=CE_RISE)

        # Normal mode knows one document shape and reports this one as a broken
        # passport, which is the honest answer for a mode that has no other model.
        assert normal.json()["profile"] == "eu-dpp"
        assert normal.json()["conforms"] is False

        assert ce_rise.json()["profile"] == "ce-rise:product-system"
        assert ce_rise.json()["conforms"] is True

    def test_a_passport_is_still_checked_as_a_passport(self, client) -> None:
        """The two vocabularies do not intersect at a single top-level term.

        So routing must send a passport to the regulatory profile in both modes; a
        mode that checked it against a CE-RISE model would report conformance for a
        document it had not understood, because those models require nothing.
        """
        for headers in (NORMAL, CE_RISE):
            body = client.post("/api/validate", json={"dpp": self.PASSPORT}, headers=headers).json()
            assert body["profile"] == "eu-dpp"

    def test_an_unrecognised_record_falls_back_rather_than_conforming_vacuously(
        self, client
    ) -> None:
        for record in ({}, {"not_a_term_anywhere": 1}):
            body = client.post("/api/validate", json={"dpp": record}, headers=CE_RISE).json()
            assert body["profile"] == "eu-dpp"
            assert body["conforms"] is False

    def test_recognition_is_vocabulary_not_validity(self, client) -> None:
        """A broken CE-RISE document is still a CE-RISE document.

        Routing on conformance would mean the more broken a record is, the less
        likely it is to be recognised -- so a ProductSystem with one wrong type
        would be told it was missing ``dpp_id``, which helps nobody.
        """
        broken = {**self.PRODUCT_SYSTEM, "activity_references": ["not-an-object"]}
        body = client.post("/api/validate", json={"dpp": broken}, headers=CE_RISE).json()
        assert body["profile"] == "ce-rise:product-system"
        assert body["conforms"] is False
        assert body["violations"][0]["location"] == "/activity_references/0"

    def test_a_named_profile_is_honoured_exactly_in_both_modes(self, client) -> None:
        # Quietly checking something else would make a caller's "conforms" mean
        # something they did not ask for.
        for headers in (NORMAL, CE_RISE):
            body = client.post(
                "/api/validate",
                json={"dpp": self.PRODUCT_SYSTEM, "profile": "eu-dpp"},
                headers=headers,
            ).json()
            assert body["profile"] == "eu-dpp"


class TestRepairAndSynthesisInheritTheModesSchema:
    """The composer targets whatever the bound mode validates against.

    Asserted on the bound registry rather than through the endpoints, because both
    endpoints need a model call and replay has no recording for a CE-RISE document.
    What is being pinned is that neither router carries a literal default any more:
    the profile comes from the mode, so adding a mode moves all three features.
    """

    def test_the_default_profile_comes_from_the_mode(self, registry) -> None:
        normal = registry.for_mode(BackendMode.NORMAL).schemas.default_profile()
        ce_rise = registry.for_mode(BackendMode.CE_RISE).schemas.default_profile()
        assert str(normal) == "eu-dpp"
        assert str(ce_rise) == "ce-rise:auto"

    def test_no_request_model_carries_a_profile_default(self) -> None:
        """Every one of the three must default to "ask the mode", not to a literal.

        Checked on the field defaults rather than by grepping the source: a text
        search cannot tell a live default from the word appearing in a comment, and
        the first draft of this test failed on its own explanation.
        """
        from apps.api.routers.synthesize import SynthesizeRequest
        from apps.api.routers.validate import RepairRequest, ValidateRequest

        for model in (ValidateRequest, RepairRequest, SynthesizeRequest):
            field = model.model_fields["profile"]
            assert field.default is None, (
                f"{model.__name__} pins a profile default; it must ask the bound "
                f"mode, or a new mode will keep validating against the old schema"
            )

    @pytest.mark.cassette
    def test_a_synthesised_passport_is_a_passport_in_both_modes(self, recorded) -> None:
        """Routing applies to generated records too, and gets this one right.

        The composer builds EU DPP passports, so CE-RISE mode routes the result back
        to the regulatory profile. That is not the switch failing to reach synthesis
        -- it is the switch reaching it and choosing correctly.
        """
        for headers, mode in ((NORMAL, "normal"), (CE_RISE, "ce-rise")):
            response = recorded.post("/api/synthesize", json={"seed": ROUTE_SEED}, headers=headers)
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["mode"] == mode
            assert body["profile"] == "eu-dpp"
            assert body["conforms"] is True
