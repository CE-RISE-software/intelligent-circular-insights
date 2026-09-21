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


@pytest.mark.parametrize("drift", [False, True])
def test_recording_extension_preserves_old_goldens_and_manifest_notes(tmp_path, monkeypatch, drift):
    from tooling import record_llm

    directory = tmp_path / "recorded"
    directory.mkdir()
    golden = {"existing": {"value": 1}, "retired": {"value": "retained"}}
    old_manifest = {"recorded_at": "first-recording", "note": "audit history must survive"}
    (directory / "expected.json").write_text(json.dumps(golden))
    (directory / "manifest.json").write_text(json.dumps(old_manifest))
    transport = ScriptedTransport([])
    monkeypatch.setattr(record_llm, "CASSETTES", tmp_path)
    monkeypatch.setattr(record_llm, "CASE_NAMES", ("existing", "new"))
    monkeypatch.setattr(record_llm, "OpenAITransport", lambda **kw: transport)
    monkeypatch.setattr(record_llm, "dotenv_values", lambda path: {"OPENAI_API_KEY": "synthetic"})
    monkeypatch.setattr(
        record_llm,
        "run_case",
        lambda name, provider: {
            "value": 1 if name == "existing" and not drift else 2,
        },
    )
    monkeypatch.setenv("CI", "false")
    monkeypatch.setattr("sys.argv", ["record_llm", "--record", "--env-file", "unused-test.env"])
    if drift:
        with pytest.raises(ValueError, match="Replay results differ"):
            record_llm.main()
        assert json.loads((directory / "expected.json").read_text()) == golden
        assert json.loads((directory / "manifest.json").read_text()) == old_manifest
    else:
        record_llm.main()
        assert json.loads((directory / "expected.json").read_text()) == {
            **golden,
            "new": {"value": 2},
        }
        manifest = json.loads((directory / "manifest.json").read_text())
        assert manifest["recorded_at"] == old_manifest["recorded_at"]
        assert manifest["note"] == old_manifest["note"]
        assert manifest["live_attempts"] == 0
    assert not transport.requests
    assert not (directory / ".recording.lock").exists()
