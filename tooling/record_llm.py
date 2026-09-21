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
        # Golden-output handling, per case rather than wholesale.
        #
        # A case whose output *changed* is a regression and still refuses loudly.
        # A case that is *new* is merely a larger case set, and must not be treated
        # as drift: comparing the two dicts as a whole meant that adding a case
        # made the recorder fail after it had already spent the money, leaving the
        # new cassettes on disk and the golden file never updated. Whoever ran it
        # paid to be told nothing useful.
        #
        # A case that has been *removed* from CASE_NAMES keeps its golden entry.
        # Dropping it here would quietly erase the record of a response that was
        # once paid for and asserted against.
        expected_path = directory / "expected.json"
        if expected_path.exists():
            golden = json.loads(expected_path.read_text())
            drifted = [
                name
                for name in sorted(set(golden) & set(results))
                if canonical(golden[name]) != canonical(results[name])
            ]
            if drifted:
                raise ValueError(
                    "Replay results differ from the golden output for: "
                    + ", ".join(drifted)
                    + ". Review the change; do not overwrite."
                )
            added = sorted(set(results) - set(golden))
            retired = sorted(set(golden) - set(results))
            if added or retired:
                extended = {**golden, **{name: results[name] for name in added}}
                expected_path.write_text(
                    json.dumps(extended, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                if added:
                    print(f"golden output extended: {', '.join(added)}", flush=True)
                if retired:
                    print(
                        "golden entries kept for cases no longer in CASE_NAMES: "
                        + ", ".join(retired),
                        flush=True,
                    )
        else:
            expected_path.write_text(canonical(results) + "\n", encoding="utf-8")

        # The manifest is rewritten every run, keeping the first recording date so
        # the provenance of the original capture is not lost to a later one.
        manifest = directory / "manifest.json"
        now = datetime.now(timezone.utc).isoformat()
        first_recorded = now
        previous_manifest: dict[str, Any] = {}
        if manifest.exists():
            previous_manifest = json.loads(manifest.read_text())
            first_recorded = previous_manifest.get("recorded_at", now)
        manifest.write_text(
            canonical(
                {
                    **previous_manifest,
                    "origin": "Real OpenAI responses to synthetic/public demo inputs",
                    "recorded_at": first_recorded,
                    "updated_at": now,
                    "cases": list(CASE_NAMES),
                    "max_calls": 40,
                    "max_reserved_usd": 1.0,
                    # Cumulative across every run, failed attempts included: the
                    # ledger is an audit record of spend, not of success.
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
