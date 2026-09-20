"""Stable synthetic/public demo inputs shared by deliberate recording and replay."""

import json
from pathlib import Path

from ici_core.domain.evidence import ContextPack, Evidence, EvidenceKind
from ici_core.domain.ids import EvidenceId
from ici_llm.prompts import canonical

CASSETTES = Path(__file__).resolve().parent / "cassettes"
DEMO_RECORD = {
    "schema_version": "ce-rise-demo-0.1",
    "dpp_id": "synthetic-demo-dpp-001",
    "product": {
        "id": "SYNTHETIC-BAT-001",
        "brand": "Demo",
        "model": "Example 1",
        "category": "battery",
    },
    "materials": [{"name": "Steel", "share_pct": 100}],
    "compliance": {"standards": ["DEMO-STANDARD-1"], "ce_marking": False},
    "notes": "Synthetic test record, not a claim about any real product or regulatory conformity.",
}


def record_pack(record=DEMO_RECORD):
    return ContextPack(
        (
            Evidence(
                EvidenceId("record:1"),
                EvidenceKind.FACT,
                canonical(record),
                "fixture:synthetic-demo-record",
            ),
        )
    )


def search_pack():
    return ContextPack(
        (
            Evidence(
                EvidenceId("e1"),
                EvidenceKind.FACT,
                "The battery pack has a declared capacity of 60 kWh.",
                "fixture:capacity",
            ),
            Evidence(
                EvidenceId("e2"),
                EvidenceKind.CALC_STEP,
                "The battery pack's estimated recyclability is 85 percent.",
                "fixture:recyclability",
            ),
        )
    )


SEARCH_QUESTIONS = {
    "capacity": "What is the battery pack's declared capacity?",
    "recyclability": "What is its estimated recyclability?",
    "unanswerable": "What is the battery's warranty period?",
}


def broken_records():
    return {
        path.stem: json.loads(path.read_text())
        for path in sorted((CASSETTES / "inputs").glob("*.json"))
    }
