# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The legacy guard predicates, snapshotted as a parity oracle.

**Do not edit, and do not import this from application code.** It exists so that
`tests/unit/llm/test_guards.py` can check the rewritten guards against what the
demo actually did, from a checkout that does not sit beside the demo.

Extracted by AST from `CE-RISE-Demo/backend/api/search.py` — definitions only, so
nothing here imports or boots the legacy API. The test prefers the live legacy
source when it is present, since that also catches the demo drifting away from
this snapshot; this is the fallback.

Source file sha256: 704f49866c2f4ef00ddfe00247985f27a7e3b28b5fe561d5e107e75235f65566
Snapshotted: 2026-09-21
Names: _CITATION_BLOCK_RE, _CITATION_SEPARATOR_RE, _EVIDENCE_ID_RE, _RELIABLE_HINT_KINDS, _asks_unsupported_requirement, _invalid_evidence_citations, _looks_like_header_copy, _misses_reliable_hint
"""

from __future__ import annotations

import re
from typing import Any, Dict, List  # noqa: F401,UP035 - the legacy signatures use these

_RELIABLE_HINT_KINDS = {"direct", "carbon", "extracted", "memory", "abstain"}

_CITATION_BLOCK_RE = re.compile(r"\[([^\[\]\r\n]+)\]")

_CITATION_SEPARATOR_RE = re.compile(r"\s*(?:[;,]|\band\b)\s*", re.IGNORECASE)

_EVIDENCE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*")

def _invalid_evidence_citations(
    answer: str,
    evidence: List[Dict[str, Any]],
    *,
    require_citation: bool = False,
) -> List[str]:
    """Return bracketed citations that do not name returned evidence ids.

    The answer prompt defines a citation as one or more exact evidence ids in
    square brackets.  Multiple ids may be separated by commas, semicolons, or
    ``and``.  Other bracketed forms are rejected conservatively because they
    cannot be resolved to an audit-card id.
    """
    available_ids = {
        str(item.get("id", "")).strip()
        for item in evidence
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    blocks = _CITATION_BLOCK_RE.findall(answer or "")
    if require_citation and not blocks:
        return ["missing-citation"]

    invalid: List[str] = []
    for block in blocks:
        cited_ids = [part.strip() for part in _CITATION_SEPARATOR_RE.split(block)]
        if not cited_ids or any(not _EVIDENCE_ID_RE.fullmatch(item) for item in cited_ids):
            invalid.append(block.strip())
            continue
        invalid.extend(item for item in cited_ids if item not in available_ids)
    return list(dict.fromkeys(invalid))

def _looks_like_header_copy(answer: str) -> bool:
    low = (answer or "").strip().lower()
    if not low:
        return True
    return (
        low.startswith("digital product passport")
        or "====" in low
        or low.startswith("1) product identification")
        or low.startswith("important note")
    )

def _misses_reliable_hint(query: str, answer: str, hint: str, kind: str) -> bool:
    if kind not in {"direct", "carbon", "extracted", "memory", "abstain"} or not hint:
        return False
    low_answer = (answer or "").lower()
    low_query = (query or "").lower()
    if kind == "abstain":
        return not low_answer.startswith("insufficient evidence")
    if low_answer.startswith("insufficient evidence"):
        return True
    if kind == "carbon" and any(t in low_query for t in ("recycling", "recyclability", "end-of-life", "end of life")):
        return "recycl" not in low_answer or "70" not in low_answer
    if kind == "extracted" and "chemistry" in low_query:
        return "lithium" not in low_answer and "nmc" not in low_answer
    if kind == "extracted" and "refrigerant" in low_query:
        if "r290" in hint.lower() and "r290" not in low_answer:
            return True
        asks_service = any(
            term in low_query
            for term in ("service", "servicing", "maintain", "maintenance", "repair")
        )
        if asks_service:
            safety_terms = ("qualified", "ventilat", "ignition", "leak")
            return sum(term in low_answer for term in safety_terms) < 2
    asks_material_composition = (
        "made of" in low_query
        or "built from" in low_query
        or bool(re.search(r"\b(?:materials?|composition|substances?)\b", low_query))
    )
    if kind == "extracted" and asks_material_composition and "bill of materials" in hint.lower():
        def normalize_materials(text: str) -> str:
            return (
                text.lower()
                .replace("aluminium", "aluminum")
                .replace("plastics", "plastic")
                .replace("electronics", "electronic")
                .replace("elastomers", "elastomer")
            )

        normalized_hint = normalize_materials(hint)
        normalized_answer = normalize_materials(answer)
        material_terms = (
            "steel", "aluminum", "copper", "plastic", "electronic",
            "elastomer", "r290",
        )
        required_terms = [term for term in material_terms if term in normalized_hint]
        if any(term not in normalized_answer for term in required_terms):
            return True
        hint_without_citations = re.sub(r"\[[^\]]+\]", "", hint)
        required_values = set(re.findall(r"\b\d+(?:\.\d+)?\b", hint_without_citations))
        return any(value not in normalized_answer for value in required_values)
    if kind == "direct" and "wireless" in low_query and "test" in low_query:
        return "yes" not in low_answer or "wireless" not in low_answer
    if kind == "memory" and any(t in low_query for t in ("component", "components", "include", "includes", "uses", "use")):
        if low_answer.startswith("insufficient evidence"):
            return True
        identifiers = [
            x for x in re.findall(r"\b[A-Za-z]+[A-Za-z0-9_-]*\d+\b", hint)
            if not x.lower().startswith("product")
        ]
        return bool(identifiers) and not any(x.lower() in low_answer for x in identifiers[:3])
    return False

def _asks_unsupported_requirement(query: str, kind: str) -> bool:
    if kind == "direct":
        return False
    low = (query or "").lower()
    asks_requirement = any(t in low for t in ("require", "requires", "required", "need", "needed"))
    asks_step_or_test = any(t in low for t in ("test", "step"))
    return asks_requirement and asks_step_or_test
