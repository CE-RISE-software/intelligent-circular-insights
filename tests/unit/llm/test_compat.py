import pytest

from ici_llm.compat import grounded_chat_kwargs, structured_options, temperature_kwargs
from ici_llm.routing import ModelRouter


@pytest.mark.parametrize(
    "model,expected",
    [
        ("gpt-4o-mini", {"max_completion_tokens": 512, "temperature": 0.0}),
        ("gpt-5", {"max_completion_tokens": 512, "reasoning_effort": "minimal"}),
        ("gpt-5-mini", {"max_completion_tokens": 512}),
    ],
)
def test_exact_chat_options(model, expected):
    assert grounded_chat_kwargs(model, 0.0, 512) == expected


def test_gpt5_structured_compatibility():
    assert structured_options("gpt-5", 4096) == (
        "responses",
        {
            "max_output_tokens": 4096,
            "text": {"format": {"type": "json_object"}},
            "reasoning": {"effort": "minimal"},
        },
    )


def test_mini_structured_compatibility():
    assert structured_options("gpt-4o-mini", 4096) == (
        "chat",
        {
            "max_completion_tokens": 4096,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        },
    )


def test_temperature_family_rule():
    assert temperature_kwargs("GPT-5-mini", 0.5) == {}
    assert temperature_kwargs("gpt-4o-mini", 0.5) == {"temperature": 0.5}


def test_unknown_model_falls_back_and_warns(caplog):
    router = ModelRouter()
    assert router.resolve("not-a-model") == "gpt-4o-mini"
    assert "falling back" in caplog.text
    assert router.resolve("gpt-5") == "gpt-5"


def test_invalid_default_fails_at_startup():
    with pytest.raises(ValueError):
        ModelRouter(default="unknown")
