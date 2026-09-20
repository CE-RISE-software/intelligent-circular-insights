import pytest
from tests.llm_scenarios import DEMO_RECORD

pytestmark = pytest.mark.cassette


def test_recorded_synthesis_is_schema_valid_and_evidence_backed(replay_case):
    result = replay_case("synthesis:grounded")
    assert result["record"] == DEMO_RECORD
    assert result["support"]
    assert all(s["source_pointer"] == s["path"] for s in result["support"])


def test_recorded_gpt5_structured_compatibility(replay_case):
    assert replay_case("compat:gpt5") == {"capacity_kwh": 60}


def test_recorded_embedding_dimensions_and_values(replay_case):
    assert replay_case("embeddings:openai")["dimensions"] == 1536
