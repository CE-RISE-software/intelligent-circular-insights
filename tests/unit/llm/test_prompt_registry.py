from pathlib import Path

import pytest
import yaml

from ici_llm.audit import AuditLog
from ici_llm.prompts import PromptRegistry

PROMPTS = Path(__file__).resolve().parents[3] / "packages/ici_llm/prompts"


@pytest.mark.parametrize("path", sorted(PROMPTS.glob("*.md")), ids=lambda p: p.stem)
def test_every_prompt_renders_and_its_hash_can_be_audited(path):
    metadata = yaml.safe_load(path.read_text().split("---", 2)[1])
    assert {"id", "version", "model_families", "purpose", "variables"} <= metadata.keys()
    prompt = PromptRegistry().render(path.stem, **dict.fromkeys(metadata["variables"], "{}"))
    audit = AuditLog()
    audit.prompt(prompt)
    assert prompt.hash in audit.hashes
    assert prompt.id in str(audit.steps)
    assert len(prompt.hash) == 64


def test_no_persona_prompt_text_in_python_packages():
    packages = PROMPTS.parents[1]
    assert not [p for p in packages.rglob("*.py") if "You are" in p.read_text()]
