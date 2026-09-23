# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Validating against the real CE-RISE data models.

Until this landed, the CE-RISE models were *catalogued and routed* but nothing
validated against them: Validate, Repair and Synthesize all checked a hand-written
EU DPP schema. The models are now generated to JSON Schema by
`tooling/build_ce_rise_profiles.py` and offered as profiles.

The point these tests exist to pin down is that the two kinds of profile answer
**different questions**, and neither is a substitute for the other:

* `eu-dpp` declares required fields, so it answers *is this passport complete?*
* `ce-rise:<model>` declares none, so it answers *does this use CE-RISE vocabulary
  correctly?* — and an empty object conforms to it.

That is a property of the upstream models, not a gap in this code, and it is
asserted here rather than described in a comment so that nobody later "fixes" the
CE-RISE profiles by inventing required fields the consortium did not declare.
"""

from __future__ import annotations

import json

import pytest
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient

from ici_substrates.registry.schemas import (
    CE_RISE_GENERATED,
    CE_RISE_ROOTS,
    JsonSchemaRegistry,
)

NORMAL = {"X-Backend-Mode": "normal"}
CE_RISE = {"X-Backend-Mode": "ce-rise"}


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c


def _generated() -> bool:
    return CE_RISE_GENERATED.is_dir() and any(CE_RISE_GENERATED.glob("*.json"))


pytestmark = pytest.mark.skipif(
    not _generated(),
    reason="run `python -m tooling.build_ce_rise_profiles` to generate the CE-RISE profiles",
)


class TestTheProfilesComeFromTheRealModels:
    def test_every_generated_schema_names_its_source(self) -> None:
        # The provenance travels in the artefact, so a reader who opens one does not
        # have to find the generator to learn what produced it or under what terms.
        for path in sorted(CE_RISE_GENERATED.glob("*.json")):
            comment = json.loads(path.read_text()).get("$comment", "")
            assert "build_ce_rise_profiles.py" in comment, path.name
            assert "CC-BY-NC-4.0" in comment, path.name

    def test_only_models_with_a_declared_root_are_offered(self, client) -> None:
        """Eleven of the seventeen models are class libraries, not documents.

        They declare no `tree_root`, so there is no defined shape for "a valid X".
        Inventing one would assert a document shape the authors did not.
        """
        offered = {
            p["id"]
            for p in client.get("/api/validate/profiles", headers=NORMAL).json()["profiles"]
            if p["id"].startswith("ce-rise:")
        }
        assert offered == {f"ce-rise:{name}" for name in CE_RISE_ROOTS}
        assert len(offered) < len(list(CE_RISE_GENERATED.glob("*.json")))

    def test_each_offered_profile_resolves_to_its_root_class(self) -> None:
        registry = JsonSchemaRegistry()
        for name, root in CE_RISE_ROOTS.items():
            from ici_core.domain.ids import ProfileId

            schema = registry._ce_rise_schema(ProfileId(f"ce-rise:{name}"))
            assert schema is not None, name
            # Rooted at the class, with every neighbour still reachable by $ref.
            assert "$defs" in schema and root in schema["$defs"], name

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_the_profiles_are_offered_in_both_modes(self, client, headers) -> None:
        # Vocabulary is not mode-specific: a CE-RISE model is the consortium's model
        # whichever backend is answering.
        layers = {
            p["id"]: p["layer"]
            for p in client.get("/api/validate/profiles", headers=headers).json()["profiles"]
        }
        assert layers["ce-rise:product-system"] == "ce-rise-vocabulary"
        assert layers["eu-dpp"] == "regulatory"


class TestTheTwoProfilesAnswerDifferentQuestions:
    """The finding worth keeping, asserted so it cannot be quietly "fixed"."""

    def test_eu_dpp_catches_an_incomplete_passport(self, client) -> None:
        body = client.post(
            "/api/validate", json={"dpp": {}, "profile": "eu-dpp"}, headers=NORMAL
        ).json()
        assert body["conforms"] is False
        missing = {v["message"] for v in body["violations"]}
        assert any("dpp_id" in m for m in missing)

    def test_a_ce_rise_model_does_not_and_should_not(self, client) -> None:
        """An empty object conforms. That is the upstream models' choice.

        They declare no required fields — they are vocabularies to draw from, not
        completeness contracts. Asserting it here means a later change that adds
        required fields to the *generated* schemas fails loudly, because that would
        be this repository inventing consortium policy.
        """
        body = client.post(
            "/api/validate", json={"dpp": {}, "profile": "ce-rise:product-system"}, headers=NORMAL
        ).json()
        assert body["conforms"] is True
        assert body["violations"] == []

    def test_a_ce_rise_model_catches_a_property_it_has_never_heard_of(self, client) -> None:
        body = client.post(
            "/api/validate",
            json={"dpp": {"not_a_ce_rise_field": 1}, "profile": "ce-rise:product-system"},
            headers=NORMAL,
        ).json()
        assert body["conforms"] is False
        assert any("Additional properties" in v["message"] for v in body["violations"])

    def test_a_ce_rise_model_catches_a_wrong_type_on_a_real_field(self, client) -> None:
        body = client.post(
            "/api/validate",
            json={"dpp": {"activity_references": 12345}, "profile": "ce-rise:product-system"},
            headers=NORMAL,
        ).json()
        assert body["conforms"] is False
        violation = next(v for v in body["violations"] if v["location"] == "/activity_references")
        assert violation["kind"] == "type_mismatch"

    def test_the_material_share_rule_belongs_to_eu_dpp_only(self, client) -> None:
        """A rule this repository added is not imputed to the consortium's model."""
        record = {"materials": [{"name": "Steel", "share_pct": 10}]}
        ce_rise = client.post(
            "/api/validate",
            json={"dpp": record, "profile": "ce-rise:product-system"},
            headers=NORMAL,
        ).json()
        assert not any("95 to 105" in v["message"] for v in ce_rise["violations"])


class TestAnUnknownProfileIsStillRefused:
    def test_a_model_without_a_root_is_not_a_profile(self, client) -> None:
        # product-profile generates fine but declares no tree_root, so it is not
        # offered and asking for it is an error rather than a silent pass.
        body = client.post(
            "/api/validate",
            json={"dpp": {}, "profile": "ce-rise:product-profile"},
            headers=NORMAL,
        ).json()
        assert body["conforms"] is False
        assert "no such profile" in body["violations"][0]["message"]

    def test_a_nonsense_profile_is_refused(self, client) -> None:
        body = client.post(
            "/api/validate", json={"dpp": {}, "profile": "ce-rise:does-not-exist"}, headers=NORMAL
        ).json()
        assert "no such profile" in body["violations"][0]["message"]


class TestViolationsAreOrderedWithoutRenderingTheSchema:
    """The sort key is the whole of this, and it was a 120x defect.

    ``sorted(..., key=str)`` looks harmless until the schema is large.
    ``ValidationError.__str__`` renders the failing schema *and* the instance into
    its message, so one error against a generated CE-RISE model stringifies to
    roughly 900,000 characters; sorting a single violation cost 60 ms, and a routed
    check that consults six candidates spent about 290 ms formatting strings it
    then threw away. Normal mode never showed it, because the hand-written EU DPP
    schema is small enough for the cost to hide.

    Asserted on the key rather than on a stopwatch: a timing threshold is flaky on
    a loaded machine, and what actually has to stay true is that ordering never
    renders the schema.
    """

    def test_the_sort_key_does_not_stringify_the_error(self) -> None:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry

        from ici_core.domain.ids import ProfileId
        from ici_substrates.registry.schemas import _error_order

        registry = JsonSchemaRegistry()
        schema = registry._ce_rise_schema(ProfileId("ce-rise:lci-dataset"))
        assert schema is not None
        validator = Draft202012Validator(
            schema, format_checker=FormatChecker(), registry=Registry()
        )
        error = next(validator.iter_errors({"a_term_this_model_never_declared": 1}))

        # The trap, measured rather than described.
        assert len(str(error)) > 100_000
        assert len(str(_error_order(error))) < 500

    def test_violations_arrive_grouped_by_where_they_are(self, client) -> None:
        """Ordering by location is also the order a reader repairs in."""
        record = {
            "lci_dataset_identifier": 1,
            "lci_dataset_name": 2,
            "activities": "not a list",
        }
        body = client.post(
            "/api/validate",
            json={"dpp": record, "profile": "ce-rise:lci-dataset"},
            headers=NORMAL,
        ).json()
        locations = [v["location"] for v in body["violations"]]
        assert locations == sorted(locations)
