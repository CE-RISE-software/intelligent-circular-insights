import ast
import re
from pathlib import Path

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat

from ici_core.domain.evidence import ContextPack
from ici_llm.audit import AuditLog
from ici_llm.composition import GroundedComposer, GroundedPrompt
from ici_llm.errors import Refused
from ici_llm.guards import (
    AnswerHint,
    asks_unsupported_requirement,
    grounded_hint,
    invalid_evidence_citations,
    looks_like_header_copy,
    misses_reliable_hint,
)
from ici_llm.provider import OpenAIProvider

LEGACY_NAMES = {
    "_invalid_evidence_citations",
    "_looks_like_header_copy",
    "_misses_reliable_hint",
    "_asks_unsupported_requirement",
    "_RELIABLE_HINT_KINDS",
    "_CITATION_BLOCK_RE",
    "_CITATION_SEPARATOR_RE",
    "_EVIDENCE_ID_RE",
}

LEGACY_SOURCE = Path(__file__).resolve().parents[4] / "CE-RISE-Demo/backend/api/search.py"
LEGACY_SNAPSHOT = Path(__file__).resolve().parents[2] / "fixtures/legacy_search_predicates.py"


def _nodes(path: Path) -> list:
    """The predicate definitions, as AST. Nothing here imports or boots the API."""
    tree = ast.parse(path.read_text())
    return [
        n
        for n in tree.body
        if (isinstance(n, ast.FunctionDef) and n.name in LEGACY_NAMES)
        or (
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in LEGACY_NAMES for t in n.targets)
        )
    ]


def _predicates(path: Path) -> dict:
    """Execute only the pure predicate definitions, never import or boot the API."""
    namespace = {"re": re, "List": list, "Dict": dict, "Any": object}
    module = ast.Module(body=_nodes(path), type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


@pytest.fixture
def legacy():
    """The behaviour these guards replaced, as the oracle to compare against.

    Prefers the live demo source, because that also catches the demo drifting away
    from what we believe it does. Falls back to the committed snapshot, so a
    standalone clone still verifies parity instead of skipping it — the suite in a
    released repository must check "the current features are not broken", which is
    the whole point of these tests, not go quiet about it.
    """
    path = LEGACY_SOURCE if LEGACY_SOURCE.is_file() else LEGACY_SNAPSHOT
    assert path.is_file(), (
        "neither the legacy source nor its snapshot is present; "
        "regenerate the snapshot from CE-RISE-Demo/backend/api/search.py"
    )
    return _predicates(path)


def test_the_snapshot_matches_the_legacy_source_when_both_are_present() -> None:
    """The fallback is only trustworthy while it still agrees with the original.

    Skips in a standalone clone — there is nothing to compare against there — but
    in the monorepo, where both exist, a demo change that moves these predicates
    fails here rather than silently invalidating the snapshot the released repo
    ships with.
    """
    if not LEGACY_SOURCE.is_file():
        pytest.skip("the legacy demo is not beside this checkout")

    def by_name(path: Path) -> dict[str, str]:
        # ast.dump, not bytecode: comparing __code__.co_code missed a flipped
        # `return True` → `return False`, because the constant lives in co_consts
        # rather than in the opcodes. The dump carries structure *and* constants,
        # and ignores formatting and comments, which is exactly the line we want.
        out = {}
        for node in _nodes(path):
            key = node.name if isinstance(node, ast.FunctionDef) else node.targets[0].id
            out[key] = ast.dump(node)
        return out

    live, snapshot = by_name(LEGACY_SOURCE), by_name(LEGACY_SNAPSHOT)
    assert set(live) == set(snapshot), (
        "the demo defines a different set of predicates than the snapshot; "
        "regenerate tests/fixtures/legacy_search_predicates.py"
    )
    drifted = sorted(name for name in live if live[name] != snapshot[name])
    assert not drifted, (
        f"these predicates have changed in the demo: {', '.join(drifted)}. "
        f"Regenerate tests/fixtures/legacy_search_predicates.py, and check whether "
        f"the rewritten guards need to follow."
    )


@pytest.mark.parametrize(
    "answer,expected",
    [
        ("Capacity 60 kWh [e1].", ()),
        ("Both [e1 AND e2].", ()),
        ("Capacity [missing].", ("missing",)),
        ("Capacity [e1 e2].", ("e1 e2",)),
        ("No citation.", ("missing-citation",)),
    ],
)
def test_citations_match_legacy(legacy, evidence_items, answer, expected):
    pack = ContextPack(tuple(evidence_items))
    assert invalid_evidence_citations(answer, pack, require_citation=True) == expected
    assert (
        tuple(
            legacy["_invalid_evidence_citations"](
                answer, [{"id": e.id} for e in pack.items], require_citation=True
            )
        )
        == expected
    )


@pytest.mark.parametrize(
    "answer",
    [
        "",
        "Digital Product Passport — Battery",
        "====",
        "1) Product identification",
        "Important note: read this",
        "Capacity 60 kWh [e1].",
    ],
)
def test_header_guard_matches_legacy(legacy, answer):
    assert looks_like_header_copy(answer) == legacy["_looks_like_header_copy"](answer)


@pytest.mark.parametrize(
    "query,answer,text,kind,misses",
    [
        ("chemistry?", "Lithium NMC [e1].", "NMC [e1].", "extracted", False),
        ("chemistry?", "A battery [e1].", "NMC [e1].", "extracted", True),
        (
            "refrigerant service?",
            "R290; qualified staff check leaks [e1].",
            "R290 [e1]",
            "extracted",
            False,
        ),
        ("refrigerant service?", "R290 [e1].", "R290 [e1]", "extracted", True),
        ("refrigerant?", "Other gas [e1].", "R290 [e1]", "extracted", True),
        ("wireless test?", "Yes, wireless [e1].", "Yes [e1].", "direct", False),
        ("wireless test?", "No [e1].", "Yes [e1].", "direct", True),
        ("components?", "Cell12 [e1].", "Cell12 [e1].", "memory", False),
        ("components?", "Battery [ev].", "Cell12 [ev].", "memory", True),
        ("anything?", "A fact [e1].", "No evidence", "abstain", True),
        ("anything?", "Insufficient evidence.", "No evidence", "abstain", False),
        ("materials?", "Steel 5% [e1]", "Bill of materials: steel 5% [e1]", "extracted", False),
        ("materials?", "Other [e1]", "Bill of materials: steel 5% [e1]", "extracted", True),
        ("q", "Insufficient evidence.", "60 [e1]", "direct", True),
        ("q", "Other [e1]", "60 [e1]", "untrusted", False),
    ],
)
def test_hint_predicates_match_legacy(legacy, query, answer, text, kind, misses):
    assert misses_reliable_hint(query, answer, AnswerHint(text, kind)) is misses
    assert legacy["_misses_reliable_hint"](query, answer, text, kind) is misses


def test_corrected_numeric_guards():
    assert misses_reliable_hint(
        "components?", "Battery [e1].", AnswerHint("Cell12 [e1].", "memory")
    )
    assert not misses_reliable_hint(
        "recyclability?", "Recyclability 85% [e1]", AnswerHint("Recyclability 85% [e1]", "carbon")
    )
    assert misses_reliable_hint(
        "materials?", "Steel 55% [e1]", AnswerHint("Bill of materials: steel 5% [e1]", "extracted")
    )


@pytest.mark.parametrize(
    "query,kind,expected",
    [
        ("Which tests are required?", "extracted", True),
        ("Which tests are required?", "direct", False),
        ("What is the capacity?", "", False),
    ],
)
def test_requirement_guard_matches_legacy(legacy, query, kind, expected):
    assert asks_unsupported_requirement(query, kind) is expected
    assert legacy["_asks_unsupported_requirement"](query, kind) is expected


@pytest.mark.parametrize(
    "answer", ["Wrong [unknown].", "Digital Product Passport [e1]", "Insufficient evidence."]
)
def test_guarded_extraction_is_a_candidate_for_final_verification(evidence_items, answer):
    pack = ContextPack(tuple(evidence_items))
    hint = AnswerHint("The declared capacity is 60 kWh [e1].", "extracted")
    audit = AuditLog()
    result = GroundedComposer(OpenAIProvider(ScriptedTransport([chat(answer)])), audit).compose(
        GroundedPrompt("capacity?", pack, hint)
    )
    assert result.used_fallback and result.answer == hint.text
    assert "grounded_extractive_fallback" in str(audit.steps)
    assert grounded_hint(hint, pack)
    assert not grounded_hint(AnswerHint("Uncited", "direct"), pack)


def test_refusal_not_bypassed_and_unsupported_requirement_makes_no_call(evidence_items):
    pack = ContextPack(tuple(evidence_items))
    transport = ScriptedTransport([chat(refusal="declined")])
    composer = GroundedComposer(OpenAIProvider(transport), AuditLog())
    with pytest.raises(Refused):
        composer.compose(GroundedPrompt("Which tests are required?", pack))
    assert not transport.requests
    with pytest.raises(Refused):
        composer.compose(GroundedPrompt("capacity?", pack, AnswerHint("60 kWh [e1]", "direct")))
    assert len(transport.requests) == 1
