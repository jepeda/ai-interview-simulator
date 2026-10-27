import pytest

from drills.ex06_none_handling import (
    display_copay,
    first_present,
    member_id_or_self_pay,
    primary_phone,
)


@pytest.mark.parametrize(
    ("cents", "expected"),
    [(None, "Unknown"), (0, "$0.00"), (2500, "$25.00"), (5, "$0.05"), (123456, "$1,234.56")],
)
def test_display_copay(cents, expected):
    assert display_copay(cents) == expected


def test_primary_phone_happy_path():
    patient = {"contact": {"phones": [{"number": "555-0100"}, {"number": "555-0199"}]}}
    assert primary_phone(patient) == "555-0100"


@pytest.mark.parametrize(
    "patient",
    [
        {},
        {"contact": None},
        {"contact": {}},
        {"contact": {"phones": None}},
        {"contact": {"phones": []}},
        {"contact": {"phones": [{}]}},
    ],
)
def test_primary_phone_missing_levels(patient):
    assert primary_phone(patient) is None


def test_first_present_empty_string_counts():
    assert first_present(None, "", "x") == ""


def test_first_present_all_none():
    assert first_present(None, None) is None
    assert first_present() is None


def test_first_present_returns_first_value():
    assert first_present(None, "a", "b") == "a"


@pytest.mark.parametrize(
    ("patient", "expected"),
    [
        ({"member_id": " W123 "}, "W123"),
        ({"member_id": None}, "SELF-PAY"),
        ({"member_id": "   "}, "SELF-PAY"),
        ({}, "SELF-PAY"),
    ],
)
def test_member_id_or_self_pay(patient, expected):
    assert member_id_or_self_pay(patient) == expected
