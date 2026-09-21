# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Configuration, in one place.

Nothing outside this module calls ``os.getenv``. That rule exists because the
current codebase reads environment variables from inside business logic, which
makes a service impossible to test without a matching environment and impossible
to reason about without grepping.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # -- service
    log_level: str = "INFO"
    cors_allow_origins: str = "http://localhost:5173,http://localhost:8000"

    # -- modes
    backend_mode_default: str = "normal"
    backend_modes_allowed: str = "normal,ce-rise"

    # -- models (Codex owns everything downstream of these)
    llm_model_default: str = "gpt-4o-mini"
    llm_model_allowed: str = "gpt-4o-mini,gpt-5"
    openai_api_key: str = ""
    llm_disabled: bool = False

    # -- cassettes: the reason the test suite costs nothing to run
    llm_cassette_mode: Literal["replay", "record", "live"] = "replay"
    """'replay' (default, no network), 'record', or 'live'."""
    llm_cassette_dir: str = "tests/cassettes"

    # -- selective decision
    default_tau: float = Field(default=0.5, ge=0, le=1, allow_inf_nan=False)

    # -- retrieval
    max_context_chars: int = 12_000
    max_passages: int = 6

    @property
    def allowed_modes(self) -> tuple[str, ...]:
        return tuple(m.strip() for m in self.backend_modes_allowed.split(",") if m.strip())

    @property
    def allowed_models(self) -> tuple[str, ...]:
        return tuple(m.strip() for m in self.llm_model_allowed.split(",") if m.strip())

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
