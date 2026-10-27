"""Part 4: cancellation (services/booking.py -> cancel_appointment)."""

from datetime import UTC, datetime, timedelta

import pytest

START = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)  # Monday 09:00 in New York


@pytest.fixture
def booked(make_provider, make_patient, make_appointment):
    def _make(rate: int = 15000, status: str = "booked"):
        provider = make_provider(windows=[(0, "09:00", "12:00")], rate=rate)
        return make_appointment(provider, make_patient(), START, status=status)

    return _make


def cancel(client, appointment_id, by="patient", reason="schedule conflict"):
    return client.post(f"/appointments/{appointment_id}/cancel", json={"cancelled_by": by, "reason": reason})


def test_patient_cancels_early_no_fee(client, clock, booked):
    appointment = booked()
    clock.now = START - timedelta(hours=48)
    response = cancel(client, appointment.id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["late_cancel_fee_cents"] == 0
    assert body["cancelled_by"] == "patient"
    assert body["cancel_reason"] == "schedule conflict"
    assert datetime.fromisoformat(body["cancelled_at"]) == clock.now


def test_patient_cancels_late_pays_half(client, clock, booked):
    appointment = booked(rate=15000)
    clock.now = START - timedelta(hours=23)
    assert cancel(client, appointment.id).json()["late_cancel_fee_cents"] == 7500


def test_late_fee_rounds_half_cent_up(client, clock, booked):
    appointment = booked(rate=15001)
    clock.now = START - timedelta(hours=1)
    assert cancel(client, appointment.id).json()["late_cancel_fee_cents"] == 7501


def test_exactly_24_hours_before_is_not_late(client, clock, booked):
    appointment = booked()
    clock.now = START - timedelta(hours=24)
    assert cancel(client, appointment.id).json()["late_cancel_fee_cents"] == 0


def test_provider_cancellation_never_has_a_fee(client, clock, booked):
    appointment = booked()
    clock.now = START - timedelta(hours=1)
    body = cancel(client, appointment.id, by="provider").json()
    assert body["late_cancel_fee_cents"] == 0
    assert body["cancelled_by"] == "provider"


def test_cannot_cancel_twice(client, clock, booked):
    appointment = booked()
    clock.now = START - timedelta(hours=48)
    assert cancel(client, appointment.id).status_code == 200
    response = cancel(client, appointment.id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_transition"


@pytest.mark.parametrize("offset", [timedelta(0), timedelta(minutes=10)])
def test_cannot_cancel_once_started(client, clock, booked, offset):
    appointment = booked()
    clock.now = START + offset
    response = cancel(client, appointment.id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_transition"


def test_cannot_cancel_completed(client, clock, booked):
    appointment = booked(status="completed")
    clock.now = START - timedelta(hours=48)
    assert cancel(client, appointment.id).status_code == 409


def test_unknown_appointment(client):
    response = cancel(client, 999)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_cancelled_slot_reopens(client, clock, booked):
    appointment = booked()
    params = {"date": "2026-11-02", "tz": "America/New_York"}
    slots_before = client.get(f"/providers/{appointment.provider_id}/slots", params=params).json()["slots"]
    assert all(datetime.fromisoformat(s["starts_at"]) != START for s in slots_before)

    clock.now = START - timedelta(hours=48)
    assert cancel(client, appointment.id).status_code == 200

    slots_after = client.get(f"/providers/{appointment.provider_id}/slots", params=params).json()["slots"]
    assert any(datetime.fromisoformat(s["starts_at"]) == START for s in slots_after)
