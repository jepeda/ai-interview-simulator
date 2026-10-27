from collections import defaultdict

from drills.ex04_collections import (
    group_by_provider,
    missing_fields,
    shared_patients,
    top_diagnoses,
)


def test_group_by_provider():
    appts = [
        {"id": 1, "provider": "Lee"},
        {"id": 2, "provider": "Ng"},
        {"id": 3, "provider": "Lee"},
    ]
    assert group_by_provider(appts) == {"Lee": [1, 3], "Ng": [2]}


def test_group_by_provider_returns_plain_dict():
    result = group_by_provider([{"id": 1, "provider": "Lee"}])
    assert type(result) is dict
    assert not isinstance(result, defaultdict)


def test_top_diagnoses():
    codes = ["F41.1", "F32.0", "F41.1", "F43.1", "F32.0", "F41.1"]
    assert top_diagnoses(codes, 2) == [("F41.1", 3), ("F32.0", 2)]


def test_top_diagnoses_ties_keep_first_seen_order():
    assert top_diagnoses(["B", "A", "A", "B", "C"], 2) == [("B", 2), ("A", 2)]


def test_missing_fields_absent_and_none():
    record = {"first_name": "Ann", "last_name": None}
    required = {"first_name", "last_name", "date_of_birth"}
    assert missing_fields(record, required) == {"last_name", "date_of_birth"}


def test_missing_fields_falsy_values_are_present():
    record = {"copay_cents": 0, "notes": ""}
    assert missing_fields(record, {"copay_cents", "notes"}) == set()


def test_shared_patients():
    assert shared_patients([5, 1, 3, 3], [3, 5, 9]) == [3, 5]
    assert shared_patients([1], [2]) == []
