"""Deliberate, bounded recording: python -m tooling.record_llm --help.

The ledger reserves worst-case estimated USD BEFORE each attempt, including
failed attempts. Re-running uses existing fixtures and retains the cumulative
limit. Pricing is an estimate, not a billing-system guarantee. No SDK retries.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from tests.llm_recording_cases import CASE_NAMES, run_case
from tests.llm_scenarios import CASSETTES

from ici_llm.audit import DEFAULT_PRICES
from ici_llm.cassettes import CassetteTransport
from ici_llm.errors import BudgetExceeded
from ici_llm.prompts import canonical
from ici_llm.provider import OpenAIProvider
from ici_llm.transport import OpenAITransport, Request, Transport, TransportResult


class BoundedRecorder:
    def __init__(
        self, live: Transport, ledger: Path, *, max_calls: int = 40, max_reserved_usd: float = 1.0
    ) -> None:
        if not 1 <= max_calls <= 40 or not 0 < max_reserved_usd <= 1:
            raise ValueError("recording caps must not exceed 40 calls and 1 estimated USD")
        self.live, self.ledger = live, ledger
        self.max_calls, self.max_reserved_usd = max_calls, max_reserved_usd
        self.events: list[dict[str, Any]] = (
            json.loads(ledger.read_text()) if ledger.exists() else []
        )

    def _save(self) -> None:
        temporary = self.ledger.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(canonical(self.events) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.ledger)

    def send(self, request: Request) -> TransportResult:
        model = str(request.kwargs["model"])
        rates = DEFAULT_PRICES.get(model)
        if rates is None:
            raise BudgetExceeded("Recording does not permit an unpriced model.")
        output = request.kwargs.get(
            "max_completion_tokens", request.kwargs.get("max_output_tokens", 0)
        )
        # UTF-8 bytes conservatively exceed token counts for these text-only calls.
        reserved = (
            (len(canonical(request.kwargs).encode()) + 1024) * rates[0] + output * rates[2]
        ) / 1_000_000
        if (
            len(self.events) >= self.max_calls
            or sum(e["reserved_usd"] for e in self.events) + reserved > self.max_reserved_usd
        ):
            raise BudgetExceeded("The cumulative recording ceiling was reached.")
        event = {
            "request_hash": request.key,
            "model": model,
            "reserved_usd": reserved,
            "status": "attempted",
        }
        self.events.append(event)
        self._save()
        start = time.perf_counter()
        try:
            result = self.live.send(request)
        except Exception as exc:
            event["status"] = type(exc).__name__
            self._save()
            raise
        event["status"] = "recorded"
        event["response_model"] = result.response.get("model")
        event["duration_ms"] = (time.perf_counter() - start) * 1000
        event["usage"] = result.response.get("usage") or {}
        self._save()
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record", action="store_true", help="explicitly permit bounded paid calls"
    )
    parser.add_argument("--env-file", type=Path, help="explicit local dotenv credential source")
    args = parser.parse_args()
    if not args.record or not args.env_file:
        parser.error("both --record and --env-file are required; nothing was called")
    if os.environ.get("CI", "").lower() not in {"", "0", "false"}:
        parser.error("recording is forbidden in CI")
    key = dotenv_values(args.env_file).get("OPENAI_API_KEY")
    if not key:
        parser.error("the selected credential file has no configured OpenAI key")
    directory = CASSETTES / "recorded"
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".recording.lock"
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.error("another recording holds the lock; inspect it before retrying")
    os.close(descriptor)
    try:
        recorder = BoundedRecorder(OpenAITransport(api_key=key), directory / "ledger.json")
        transport = CassetteTransport(directory, mode="record", live=recorder, secrets=(key,))
        results = {}
        for name in CASE_NAMES:
            provider = OpenAIProvider(transport)
            results[name] = run_case(name, provider)
            print(f"{name}: complete; cumulative live attempts={len(recorder.events)}", flush=True)
        expected_path = directory / "expected.json"
        if expected_path.exists():
            if canonical(json.loads(expected_path.read_text())) != canonical(results):
                raise ValueError(
                    "Replay results differ from the golden output; review, do not overwrite."
                )
        else:
            expected_path.write_text(canonical(results) + "\n", encoding="utf-8")
        manifest = directory / "manifest.json"
        if not manifest.exists():
            manifest.write_text(
                canonical(
                    {
                        "origin": "Real OpenAI responses to synthetic/public demo inputs",
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                        "cases": list(CASE_NAMES),
                        "max_calls": 40,
                        "max_reserved_usd": 1.0,
                        "live_attempts": len(recorder.events),
                        "reserved_usd": sum(e["reserved_usd"] for e in recorder.events),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
        print("Recording complete. All subsequent tests replay without a key.")
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()
