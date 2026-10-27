from datetime import date

import pytest

from drills.ex12_classes import Money, Patient


def test_money_add_returns_money():
    total = Money(2500) + Money(150)
    assert isinstance(total, Money)
    assert total.cents == 2650


def test_money_equality():
    assert Money(100) == Money(100)
    assert Money(100) != Money(101)


def test_money_repr_and_str():
    assert repr(Money(2650)) == "Money(2650)"
    assert str(Money(123456)) == "$1,234.56"
    assert str(Money(5)) == "$0.05"


def test_money_rejects_non_int():
    with pytest.raises(TypeError):
        Money(19.99)
    with pytest.raises(TypeError):
        Money("100")


def test_money_from_dollars_is_classmethod():
    assert Money.from_dollars("19.99") == Money(1999)
    assert Money.from_dollars("0.29") == Money(29)  # float math would give 28!
    assert isinstance(Money.from_dollars("1"), Money)


def test_patient_full_name_is_property():
    p = Patient("Ada", "King", date(1990, 12, 10))
    assert p.full_name == "Ada King"


def test_patient_age_before_and_on_birthday():
    p = Patient("Ada", "King", date(1990, 12, 10))
    assert p.age_on(date(2026, 12, 9)) == 35
    assert p.age_on(date(2026, 12, 10)) == 36
    assert p.age_on(date(2027, 1, 1)) == 36
