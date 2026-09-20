import json

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat
from tooling.record_llm import BoundedRecorder

from ici_llm.errors import BudgetExceeded
from ici_llm.transport import Request


def test_recording_limit_persists_across_reruns_and_no_call_after_ceiling(tmp_path):
    transport = ScriptedTransport([chat()])
    ledger = tmp_path / "ledger.json"
    request = Request("chat", {"model": "gpt-4o-mini", "max_completion_tokens": 512})
    recorder = BoundedRecorder(transport, ledger, max_calls=1)
    recorder.send(request)
    reloaded = BoundedRecorder(transport, ledger, max_calls=1)
    with pytest.raises(BudgetExceeded):
        reloaded.send(request)
    assert (
        len(transport.requests) == 1 and json.loads(ledger.read_text())[0]["status"] == "recorded"
    )


def test_dollar_reservation_prevents_first_call(tmp_path):
    transport = ScriptedTransport([])
    recorder = BoundedRecorder(transport, tmp_path / "ledger", max_reserved_usd=0.00001)
    with pytest.raises(BudgetExceeded):
        recorder.send(Request("responses", {"model": "gpt-5", "max_output_tokens": 4096}))
    assert not transport.requests
