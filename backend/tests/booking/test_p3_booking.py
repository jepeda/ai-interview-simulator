"""Part 3: booking (services/booking.py -> book_appointment)."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from booking.models import Appointment

NEW_YORK = ZoneInfo("America/New_York")
SLOT = "2026-11-02T09:00:00-05:00"  # Monday 09:00 in New York == 14:00 UTC


@pytest.fixture
def provider(make_provider):
    return make_provider(windows=[(0, "09:00", "12:00")], payers=["Aetna"], rate=15000)


@pytest.fixture
def patient(make_patient):
    return make_patient(state="NY", payer="Aetna")


def book(client, provider, patient, starts_at=SLOT, key=None):
    body = {"provider_id": provider.id, "patient_id": patient.id, "starts_at": starts_at}
    if key:
        body["idempotency_key"] = key
    return client.post("/appointments", json=body)


def error_code(response) -> str:
    return response.json()["error"]["code"]


def count_appointments(db) -> int:
    return db.scalar(select(func.count()).select_from(Appointment))


def test_book_an_open_slot(client, db, provider, patient):
    response = book(client, provider, patient)
    assert response.status_code == 201, response.text
    body = response.json()
    assert datetime.fromisoformat(body["starts_at"]) == datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
    assert datetime.fromisoformat(body["ends_at"]) == datetime(2026, 11, 2, 14, 50, tzinfo=UTC)
    assert body["status"] == "booked"
    stored = db.get(Appointment, body["id"])
    assert stored.starts_at == datetime(2026, 11, 2, 14, 0)  # naive UTC in the DB
    assert stored.created_at == datetime(2026, 10, 26, 12, 0)


def test_same_instant_in_any_offset_is_accepted(client, provider, patient):
    response = book(client, provider, patient, starts_at="2026-11-02T14:00:00Z")
    assert response.status_code == 201, response.text


def test_double_booking_is_rejected(client, db, provider, patient, make_patient):
    assert book(client, provider, patient).status_code == 201
    response = book(client, provider, make_patient())
    assert response.status_code == 409
    assert error_code(response) == "slot_unavailable"
    assert count_appointments(db) == 1


@pytest.mark.parametrize(
    "starts_at",
    [
        "2026-11-02T09:30:00-05:00",  # not on the hour
        "2026-11-02T13:00:00-05:00",  # outside the window
        "2026-11-03T09:00:00-05:00",  # Tuesday: no availability
        "2026-10-19T09:00:00-04:00",  # in the past
    ],
)
def test_times_that_are_not_open_slots(client, provider, patient, starts_at):
    response = book(client, provider, patient, starts_at=starts_at)
    assert response.status_code == 409
    assert error_code(response) == "slot_unavailable"


def test_idempotent_retry_returns_the_original(client, db, provider, patient):
    first = book(client, provider, patient, key="req-12345678")
    retry = book(client, provider, patient, key="req-12345678")
    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json()["id"] == first.json()["id"]
    assert count_appointments(db) == 1


def test_idempotency_key_reused_for_a_different_booking(client, provider, patient):
    assert book(client, provider, patient, key="req-12345678").status_code == 201
    response = book(client, provider, patient, starts_at="2026-11-02T10:00:00-05:00", key="req-12345678")
    assert response.status_code == 409
    assert error_code(response) == "idempotency_key_reused"


def test_provider_must_be_licensed_in_patient_state(client, provider, make_patient):
    response = book(client, provider, make_patient(state="CA"))
    assert response.status_code == 422
    assert error_code(response) == "not_licensed_in_state"


def test_expired_license_is_not_valid(client, make_provider, patient):
    expired = make_provider(licenses={"NY": date(2026, 10, 25)})
    response = book(client, expired, patient)
    assert response.status_code == 422
    assert error_code(response) == "not_licensed_in_state"


def test_payer_must_be_in_network(client, provider, make_patient):
    response = book(client, provider, make_patient(payer="Cigna"))
    assert response.status_code == 422
    assert error_code(response) == "payer_not_accepted"


@pytest.mark.parametrize("payer", ["AETNA", None])
def test_payer_match_is_case_insensitive_and_self_pay_is_allowed(client, provider, make_patient, payer):
    assert book(client, provider, make_patient(payer=payer)).status_code == 201


def test_unknown_provider_or_patient(client, provider, patient):
    response = client.post("/appointments", json={"provider_id": 999, "patient_id": patient.id, "starts_at": SLOT})
    assert response.status_code == 404
    assert error_code(response) == "not_found"
    response = client.post("/appointments", json={"provider_id": provider.id, "patient_id": 999, "starts_at": SLOT})
    assert response.status_code == 404


def test_naive_datetime_is_rejected(client, provider, patient):
    assert book(client, provider, patient, starts_at="2026-11-02T09:00:00").status_code == 422


def test_cancelled_slot_can_be_booked_again(client, provider, patient, make_appointment):
    make_appointment(provider, patient, datetime(2026, 11, 2, 9, 0, tzinfo=NEW_YORK), status="cancelled")
    assert book(client, provider, patient).status_code == 201
