from datetime import date

from drills.ex09_filtering import (
    all_claims_verified,
    billable_minutes,
    find_patient,
    has_overdue_invoice,
)

PATIENTS = [{"id": 1, "name": "Ann"}, {"id": 2, "name": "Bo"}, {"id": 2, "name": "Dup"}]


def test_find_patient_found_returns_first_match():
    assert find_patient(PATIENTS, 2) == {"id": 2, "name": "Bo"}


def test_find_patient_missing_returns_none():
    assert find_patient(PATIENTS, 99) is None
    assert find_patient([], 1) is None


def test_all_claims_verified():
    assert all_claims_verified([{"verified": True}, {"verified": True}]) is True
    assert all_claims_verified([{"verified": True}, {"verified": False}]) is False


def test_all_claims_verified_empty_is_true():
    assert all_claims_verified([]) is True


def test_has_overdue_invoice():
    today = date(2026, 10, 26)
    invoices = [
        {"paid": True, "due": date(2026, 9, 1)},
        {"paid": False, "due": date(2026, 10, 26)},
    ]
    assert has_overdue_invoice(invoices, today) is False
    invoices.append({"paid": False, "due": date(2026, 10, 25)})
    assert has_overdue_invoice(invoices, today) is True


def test_has_overdue_invoice_empty():
    assert has_overdue_invoice([], date(2026, 10, 26)) is False


def test_billable_minutes():
    sessions = [
        {"status": "completed", "minutes": 50, "billed": False},  # yes
        {"status": "completed", "minutes": 30, "billed": False},  # yes (boundary)
        {"status": "completed", "minutes": 20, "billed": False},  # too short
        {"status": "completed", "minutes": 60, "billed": True},  # already billed
        {"status": "no_show", "minutes": 50, "billed": False},  # not completed
    ]
    assert billable_minutes(sessions) == 80


def test_billable_minutes_empty():
    assert billable_minutes([]) == 0
