# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Claim decomposition plus deterministic citation, quote and coverage checks.

Entailment is model-assisted, not a formal proof. Structural failures always
block answering, including an empty claim list or unaccounted-for answer text.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

from ici_core.domain.claims import Claim, GroundingReport, GroundingVerdict
from ici_core.domain.errors import GenerationError
from ici_core.domain.evidence import ContextPack
from ici_core.domain.ids import ClaimId, EvidenceId
from ici_core.ports import LLMProvider
from ici_llm.audit import AuditLog
from ici_llm.prompts import PromptRegistry, canonical
from ici_llm.provider import validate_object

CLAIM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["coverage_complete", "claims"],
    "additionalProperties": False,
    "properties": {
        "coverage_complete": {"type": "boolean"},
        "claims": {
            "type": "array",
            "minItems": 1,
            "maxItems": 64,
            "items": {
                "type": "object",
                "required": ["text", "source_text", "supported", "support"],
                "additionalProperties": False,
                "properties": {
                    "text": {"type": "string", "minLength": 1},
                    "source_text": {"type": "string", "minLength": 1},
                    "supported": {"type": "boolean"},
                    "support": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["evidence_id", "quote"],
                            "additionalProperties": False,
                            "properties": {
                                "evidence_id": {"type": "string", "minLength": 1},
                                "quote": {"type": "string", "minLength": 1},
                            },
                        },
                    },
                },
            },
        },
    },
}
_CITATIONS = re.compile(r"\[([^\[\]\r\n]+)\]")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*")


def citations(text: str) -> set[str]:
    result: set[str] = set()
    for block in _CITATIONS.findall(text):
        for item in re.split(r"\s*(?:[;,]|\band\b)\s*", block, flags=re.IGNORECASE):
            # Invalid syntax stays an unresolved identifier, never disappears.
            result.add(item if _ID.fullmatch(item) else "invalid-citation")
    return result


def numbers(text: str) -> set[Decimal]:
    plain = _CITATIONS.sub("", text)
    return {
        Decimal(n.replace(",", ""))
        for n in re.findall(r"(?<![\w.])-?\d+(?:,\d{3})*(?:\.\d+)?", plain)
    }


class GroundingVerifier:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        prompts: PromptRegistry | None = None,
        audit: AuditLog | None = None,
    ) -> None:
        self.provider = provider
        self.prompts = prompts or PromptRegistry()
        self.audit = audit or AuditLog()

    def verify(self, answer: str, pack: ContextPack) -> GroundingReport:
        if not answer.strip() or not pack:
            return self._failure(answer, "empty_answer_or_evidence")
        cited = citations(answer)
        if not cited or not cited <= pack.ids:
            return self._failure(answer, "missing_or_unknown_citation")
        prompt = self.prompts.render("grounding", answer=json.dumps(answer, ensure_ascii=False))
        from ici_core.domain.trace import TraceStep

        self.audit.hashes.append(prompt.hash)
        self.audit.steps.append(
            TraceStep("prompt", canonical({"id": prompt.id, "hash": prompt.hash}))
        )
        try:
            result = validate_object(
                dict(self.provider.structured(prompt.text, pack, CLAIM_SCHEMA)), CLAIM_SCHEMA
            )
        except GenerationError:
            return self._failure(answer, "decomposition_failed")

        covered: set[int] = set()
        unresolved: list[Claim] = []
        all_quotes: list[str] = []
        rows = result["claims"]
        for index, row in enumerate(rows):
            source = row["source_text"]
            refs = tuple(EvidenceId(s["evidence_id"]) for s in row["support"])
            claim = Claim(ClaimId(f"claim:{index + 1}"), row["text"], refs)
            offset = answer.find(source)
            source_ok = offset >= 0 and bool(source.strip())
            if source_ok:
                # Account for repeated identical spans as well as unique sentences.
                while offset >= 0:
                    covered.update(range(offset, offset + len(source)))
                    offset = answer.find(source, offset + len(source))
            quotes: list[str] = []
            support_ok = bool(refs) and set(refs) <= citations(source)
            for support in row["support"]:
                evidence = pack.get(EvidenceId(support["evidence_id"]))
                quote = support["quote"]
                if evidence is None or not quote.strip() or quote not in evidence.text:
                    support_ok = False
                else:
                    quotes.append(quote)
            supported = (
                source_ok
                and support_ok
                and row["supported"]
                and bool(row["text"].strip())
                and numbers(row["text"]) <= numbers(" ".join(quotes))
            )
            if not supported:
                unresolved.append(claim)
            else:
                all_quotes.extend(quotes)

        coverage_ok = result["coverage_complete"] and all(
            i in covered for i, character in enumerate(answer) if character.isalnum()
        )
        quantities_ok = numbers(answer) <= numbers(" ".join(all_quotes))
        self.audit.guard("claim_coverage", coverage_ok)
        self.audit.guard("numeric_support", quantities_ok)
        if not coverage_ok or not quantities_ok:
            unresolved.append(Claim(ClaimId("uncovered-answer"), answer))
        self.audit.guard("grounding", not unresolved)
        total = len(rows) + int(not coverage_ok or not quantities_ok)
        return GroundingReport(
            claims_total=total,
            claims_resolved=total - len(unresolved),
            unresolved=tuple(unresolved),
            verdict=(
                GroundingVerdict.UNRESOLVED_CLAIMS
                if unresolved
                else GroundingVerdict.FULLY_GROUNDED
            ),
        )

    def _failure(self, answer: str, reason: str) -> GroundingReport:
        self.audit.guard(reason, False)
        return GroundingReport(
            claims_total=1,
            claims_resolved=0,
            unresolved=(Claim(ClaimId(reason), answer or "Empty drafted answer"),),
            verdict=GroundingVerdict.UNRESOLVED_CLAIMS,
        )
