import copy
import json

import pytest
from tests.llm_scenarios import DEMO_RECORD, broken_records, record_pack
from tests.unit.llm.conftest import ScriptedTransport, chat

from ici_core.domain.evidence import ContextPack
from ici_llm.audit import AuditLog
from ici_llm.provider import OpenAIProvider
from ici_llm.records import RecordComposer, RecordGenerationError, at_pointer


def composer(*outputs):
    transport = ScriptedTransport([chat(json.dumps(o)) for o in outputs])
    audit = AuditLog()
    return RecordComposer(OpenAIProvider(transport, audit=audit), audit=audit), transport


def test_grounded_repair_preserves_input_and_resolves_every_reference():
    record = copy.deepcopy(DEMO_RECORD)
    del record["compliance"]
    service, transport = composer(
        {
            "fills": [
                {
                    "path": "/compliance",
                    "value": DEMO_RECORD["compliance"],
                    "evidence_id": "record:1",
                    "confidence": 0.9,
                }
            ],
            "suggestions": [],
        }
    )
    result = service.repair(record, record_pack())
    assert result.conforms and result.record == DEMO_RECORD
    assert "compliance" not in record
    assert len(result.fills) == 1 and len(transport.requests) == 1
    for fill in result.fills:
        source = record_pack().get(fill.support.evidence_id)
        assert source.ref == fill.support.evidence_ref
        assert at_pointer(json.loads(source.text), fill.support.source_pointer) == fill.value


@pytest.mark.parametrize("mutation", ["fabricated", "wrong_product", "wrong_field", "bad_type"])
def test_unsupported_or_schema_invalid_repair_is_never_applied(mutation):
    record = copy.deepcopy(DEMO_RECORD)
    del record["compliance"]
    source = copy.deepcopy(DEMO_RECORD)
    value = copy.deepcopy(source["compliance"])
    if mutation == "fabricated":
        value["ce_marking"] = True
    elif mutation == "wrong_product":
        source["product"]["id"] = "OTHER"
    elif mutation == "wrong_field":
        source["elsewhere"] = source.pop("compliance")
    else:
        source["compliance"]["ce_marking"] = "true"
        value = source["compliance"]
    service, _ = composer(
        {
            "fills": [
                {"path": "/compliance", "value": value, "evidence_id": "record:1", "confidence": 1}
            ],
            "suggestions": [],
        }
    )
    result = service.repair(record, record_pack(source))
    assert not result.fills and not result.conforms and result.record == record
    assert result.rejected


def test_training_suggestions_are_low_confidence_unverified_and_never_applied():
    record = copy.deepcopy(DEMO_RECORD)
    del record["compliance"]
    prior = {
        "path": "/compliance",
        "value": {"standards": ["IEC 62133"]},
        "rationale": "Possible standard; verify scope and conformity with the manufacturer.",
        "confidence": 0.98,
    }
    service, _ = composer({"fills": [], "suggestions": [prior, prior]})
    result = service.repair(record, ContextPack())
    assert result.record == record and not result.fills and not result.conforms
    assert len(result.suggestions) == 1
    suggestion = result.suggestions[0]
    assert suggestion.confidence == 0.3 and suggestion.source == "model_training"
    assert suggestion.status == "unverified" and suggestion.requires_review
    assert "training_suggestions_not_applied" in str(service.audit.steps)


@pytest.mark.parametrize("name,record", list(broken_records().items()))
def test_three_intentionally_broken_dpps_never_get_placeholder_repairs(name, record):
    service, transport = composer()
    result = service.repair(record, ContextPack(), suggest_from_training=False)
    assert not result.conforms and result.record == record
    assert result.cannot_be_grounded and not result.fills and not result.suggestions
    assert not transport.requests


def test_schema_checks_nested_values_formats_and_material_total():
    service, _ = composer()
    assert not service.validate(DEMO_RECORD)
    record = copy.deepcopy(DEMO_RECORD)
    record["materials"][0]["share_pct"] = 50
    record["issued_at_utc"] = "yesterday"
    record["compliance"]["ce_marking"] = 1
    record["product"]["category"] = "not-a-category"
    paths = {i.path for i in service.validate(record)}
    assert {"/materials", "/issued_at_utc", "/compliance/ce_marking", "/product/category"} <= paths


def test_synthesis_checks_schema_retries_once_and_records_prompt_hashes():
    invalid = copy.deepcopy(DEMO_RECORD)
    del invalid["compliance"]
    service, transport = composer({"record": invalid}, {"record": DEMO_RECORD})
    result = service.synthesize({"product": DEMO_RECORD["product"]}, record_pack())
    assert result.record == DEMO_RECORD and result.support
    assert len(transport.requests) == 2
    retry = json.loads(transport.requests[1].kwargs["messages"][1]["content"])["instruction"]
    assert "/compliance" in retry and "required property is missing" in retry
    assert "ici.synthesis@1" in str(service.audit.steps)
    assert len(service.audit.hashes) == 4


def test_schema_valid_hallucination_is_an_error_after_one_retry():
    unsupported = copy.deepcopy(DEMO_RECORD)
    unsupported["compliance"]["ce_marking"] = True
    service, transport = composer({"record": unsupported}, {"record": unsupported})
    with pytest.raises(RecordGenerationError) as exc:
        service.synthesize({"product": DEMO_RECORD["product"]}, record_pack())
    assert len(transport.requests) == 2
    assert any(
        i.path == "/compliance/ce_marking" and i.reason == "cannot be grounded"
        for i in exc.value.issues
    )


def test_valid_record_costs_no_repair_call_and_invalid_json_numbers_are_rejected():
    service, transport = composer()
    assert service.repair(DEMO_RECORD, ContextPack()).conforms
    assert not transport.requests
    provider = OpenAIProvider(ScriptedTransport([chat('{"value":1e400}')]))
    from ici_llm.errors import InvalidOutput

    with pytest.raises(InvalidOutput):
        provider.structured("test", ContextPack(), {"type": "object"})
