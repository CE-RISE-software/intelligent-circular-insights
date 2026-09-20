import json

import pytest
from tests.llm_recording_cases import run_case
from tests.llm_scenarios import CASSETTES

from ici_llm.prompts import canonical
from ici_llm.provider import CassetteProvider


@pytest.fixture
def replay_case():
    def run(name):
        directory = CASSETTES / "recorded"
        expected = json.loads((directory / "expected.json").read_text())
        provider = CassetteProvider(directory)
        actual = run_case(name, provider)
        assert canonical(actual) == canonical(expected[name])
        assert provider.audit.cost.llm_calls == provider.audit.cost.usd == 0
        if not name.startswith("embeddings:"):
            assert provider.audit.hashes
        return actual

    return run
