import json

import pytest

from ici_core.domain.ids import DppId
from ici_substrates.records import InMemoryRepository


def test_reference_directory_loads_complete_records_and_missing_directory_is_empty(tmp_path):
    assert not InMemoryRepository.from_directory(tmp_path / "absent").list_ids()
    record = {"dpp_id": "synthetic-1", "notes": "x" * 10_000}
    (tmp_path / "reference.json").write_text(json.dumps(record))
    repository = InMemoryRepository.from_directory(tmp_path)
    assert repository.get(DppId("synthetic-1")).payload == record


@pytest.mark.parametrize(
    "payload", [[], {}, {"dpp_id": ""}, {"dpp_id": "x", "value": float("nan")}]
)
def test_invalid_reference_records_fail_closed(tmp_path, payload):
    (tmp_path / "invalid.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        InMemoryRepository.from_directory(tmp_path)


def test_duplicate_reference_ids_are_not_silently_overwritten(tmp_path):
    for name in ("one", "two"):
        (tmp_path / f"{name}.json").write_text(json.dumps({"dpp_id": "same"}))
    with pytest.raises(ValueError, match="unique"):
        InMemoryRepository.from_directory(tmp_path)
