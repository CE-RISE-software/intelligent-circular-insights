import pytest

pytestmark = pytest.mark.cassette


@pytest.mark.parametrize("case", ["capacity", "recyclability", "unanswerable"])
def test_recorded_search_is_exact_and_unsupported_question_abstains(replay_case, case):
    result = replay_case(f"search:{case}")
    assert result["decision"] == ("abstain" if case == "unanswerable" else "answer")
    if case == "capacity":
        assert "60" in result["answer"] and "declared" in result["answer"].lower()
    if case == "recyclability":
        assert "85" in result["answer"] and "estimated" in result["answer"].lower()


@pytest.mark.parametrize(
    "case,verdict",
    [
        ("paraphrase", "fully_grounded"),
        ("fabricated", "unresolved_claims"),
    ],
)
def test_real_model_judgments_pass_structural_grounding_checks(replay_case, case, verdict):
    assert replay_case(f"grounding:{case}")["verdict"] == verdict
