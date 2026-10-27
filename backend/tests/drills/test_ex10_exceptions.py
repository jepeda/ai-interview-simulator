import pytest

from drills.ex10_exceptions import (
    PatientNotFoundError,
    load_patient,
    parse_batch,
    parse_copay,
    safe_parse_copay,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("$25", 2500), ("25.00", 2500), (" $1,250.50 ", 125050), ("0.07", 7), ("$0", 0)],
)
def test_parse_copay_valid(raw, expected):
    assert parse_copay(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "abc", "$", "-5", "12.345"])
def test_parse_copay_invalid_raises_value_error(raw):
    with pytest.raises(ValueError):
        parse_copay(raw)


def test_parse_copay_error_mentions_input():
    with pytest.raises(ValueError, match="abc"):
        parse_copay("abc")


def test_safe_parse_copay():
    assert safe_parse_copay("$10") == 1000
    assert safe_parse_copay("nope") is None


def test_load_patient_found():
    assert load_patient({1: {"id": 1}}, 1) == {"id": 1}


def test_load_patient_missing_raises_custom_error_chained():
    with pytest.raises(PatientNotFoundError, match="42") as exc_info:
        load_patient({}, 42)
    assert isinstance(exc_info.value.__cause__, KeyError)


def test_parse_batch_continues_after_errors():
    parsed, errors = parse_batch(["$10", "bad", "2.50", ""])
    assert parsed == [1000, 250]
    assert len(errors) == 2
    assert "bad" in errors[0]
