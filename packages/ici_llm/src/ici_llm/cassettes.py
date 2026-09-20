# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Content-addressed fixtures. Recording is explicit and existing files win."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from ici_llm.errors import CassetteCorrupt, CassetteMiss
from ici_llm.prompts import canonical
from ici_llm.transport import Request, Transport, TransportResult

_SECRET_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "access_token",
    "refresh_token",
    "encrypted_content",
}


def redact(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        return {
            k: "[REDACTED]" if k.lower().replace("-", "_") in _SECRET_KEYS else redact(v, secrets)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", value)
        return re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~-]+", "Bearer [REDACTED]", value)
    return value


class CassetteTransport:
    def __init__(
        self,
        directory: Path,
        *,
        mode: str = "replay",
        live: Transport | None = None,
        secrets: tuple[str, ...] = (),
    ) -> None:
        if mode not in {"replay", "record"}:
            raise ValueError("cassette mode must be replay or record")
        self.directory = Path(directory)
        self.mode = mode
        self.live = live
        self.secrets = secrets

    def send(self, request: Request) -> TransportResult:
        path = self.directory / f"{request.key}.json"
        if path.exists():
            return self._read(path, request.key)
        if self.mode == "replay":
            raise CassetteMiss(f"Cassette {request.key} is missing; replay cannot use the network.")
        if self.live is None:
            raise ValueError("recording requires an explicit live transport")
        result = self.live.send(request)
        response = redact(result.response, self.secrets)
        # Requests, credentials and SDK exception bodies are never persisted.
        payload = {request.key: {"version": 1, "response": response}}
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(canonical(payload) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Atomic publication, without overwriting another recorder's fixture.
                os.link(temporary, path)
            except FileExistsError:
                return self._read(path, request.key)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return TransportResult(response, replayed=False)

    @staticmethod
    def _read(path: Path, key: str) -> TransportResult:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if set(data) != {key} or data[key]["version"] != 1:
                raise ValueError("wrong cassette identity or version")
            response = data[key]["response"]
            if not isinstance(response, dict):
                raise ValueError("response must be an object")
        except (ValueError, TypeError, KeyError, OSError):
            raise CassetteCorrupt(f"Cassette {key} is invalid; it must be reviewed.") from None
        return TransportResult(response, replayed=True)
