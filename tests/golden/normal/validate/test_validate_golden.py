import pytest
from tests.llm_scenarios import DEMO_RECORD, broken_records

pytestmark = pytest.mark.cassette


def test_recorded_grounded_fill_has_a_resolvable_source(replay_case):
    result = replay_case("repair:grounded")
    assert result["record"] == DEMO_RECORD
    assert not result["cannot_be_grounded"] and len(result["fills"]) == 1
    assert result["fills"][0]["support"]["evidence_id"] == "record:1"
    assert not result["suggestions"]


@pytest.mark.parametrize("case", list(broken_records()))
def test_real_training_based_suggestions_are_labelled_and_not_applied(replay_case, case):
    result = replay_case(f"repair:{case}")
    assert result["record"] == broken_records()[case]
    assert not result["fills"] and result["cannot_be_grounded"]
    # The model may decline to suggest a compliance claim for the battery.
    if case != "01_battery_missing_compliance":
        assert result["suggestions"]
    for suggestion in result["suggestions"]:
        assert suggestion["source"] == "model_training" and suggestion["status"] == "unverified"
        assert suggestion["requires_review"] and 0 <= suggestion["confidence"] <= 0.3
