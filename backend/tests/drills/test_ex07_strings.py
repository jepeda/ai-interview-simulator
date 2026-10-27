import pytest

from drills.ex07_strings import format_member_id, format_money, initials, mrn


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" ab1 23-4567 ", "AB1-234-567"),
        ("w12345", "W12-345"),
        ("abcd", "ABC-D"),
        ("x", "X"),
    ],
)
def test_format_member_id(raw, expected):
    assert format_member_id(raw) == expected


def test_initials():
    assert initials("mary  ann o'neil") == "M.A.O."
    assert initials("  Ada ") == "A."


@pytest.mark.parametrize(
    ("cents", "expected"),
    [(123456, "$1,234.56"), (5, "$0.05"), (0, "$0.00"), (-1250, "-$12.50"), (100000000, "$1,000,000.00")],
)
def test_format_money(cents, expected):
    assert format_money(cents) == expected


def test_mrn():
    assert mrn(42) == "MRN-000042"
    assert mrn(1234567) == "MRN-1234567"
