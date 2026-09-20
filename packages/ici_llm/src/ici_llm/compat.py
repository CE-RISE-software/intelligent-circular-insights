# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Compatibility rules ported from CE-RISE-Demo/backend/api/llm_compat.py.

Only annotations/style changed in the four original helpers. Routing between
Chat Completions and Responses also lives here, keeping model branches private.
"""

from __future__ import annotations

from typing import Any


def is_gpt5_model(model: str) -> bool:
    return model.lower().startswith("gpt-5")


def temperature_kwargs(model: str, temperature: float) -> dict[str, float]:
    if is_gpt5_model(model):
        return {}
    return {"temperature": temperature}


def grounded_chat_kwargs(
    model: str, temperature: float, max_completion_tokens: int
) -> dict[str, Any]:
    options: dict[str, Any] = {
        "max_completion_tokens": max_completion_tokens,
        **temperature_kwargs(model, temperature),
    }
    if model.lower() == "gpt-5":
        options["reasoning_effort"] = "minimal"
    return options


def gpt5_json_response_kwargs(max_output_tokens: int) -> dict[str, Any]:
    return {
        "max_output_tokens": max_output_tokens,
        "text": {"format": {"type": "json_object"}},
        "reasoning": {"effort": "minimal"},
    }


def structured_options(model: str, max_output_tokens: int) -> tuple[str, dict[str, Any]]:
    if is_gpt5_model(model):
        return "responses", gpt5_json_response_kwargs(max_output_tokens)
    return "chat", {
        **grounded_chat_kwargs(model, 0.0, max_output_tokens),
        "response_format": {"type": "json_object"},
    }
