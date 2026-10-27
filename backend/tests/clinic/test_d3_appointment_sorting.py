from datetime import datetime

from clinic.models import Appointment
from clinic.services.appointments import past_appointments, upcoming_appointments

NOW = datetime(2026, 10, 26, 12, 0)


def appt(id: int, starts_at: datetime, status: str = "scheduled") -> Appointment:
    return Appointment(
        id=id, provider_name="Dr. Lee", starts_at=starts_at, duration_minutes=50, status=status
    )


def ids(rows: list[dict]) -> list[int]:
    return [row["id"] for row in rows]


def test_upcoming_sorted_across_year_boundary():
    appts = [
        appt(1, datetime(2027, 1, 5, 10, 0)),
        appt(2, datetime(2026, 12, 15, 10, 0)),
        appt(3, datetime(2026, 11, 30, 10, 0)),
    ]
    assert ids(upcoming_appointments(appts, NOW)) == [3, 2, 1]


def test_upcoming_same_day_am_before_pm():
    appts = [
        appt(1, datetime(2026, 10, 28, 14, 0)),
        appt(2, datetime(2026, 10, 28, 9, 0)),
        appt(3, datetime(2026, 10, 28, 11, 0)),
    ]
    assert ids(upcoming_appointments(appts, NOW)) == [2, 3, 1]


def test_upcoming_excludes_cancelled():
    appts = [
        appt(1, datetime(2026, 10, 27, 9, 0), status="cancelled"),
        appt(2, datetime(2026, 10, 29, 9, 0)),
    ]
    assert ids(upcoming_appointments(appts, NOW)) == [2]


def test_appointment_exactly_now_is_upcoming():
    assert ids(upcoming_appointments([appt(1, NOW)], NOW)) == [1]


def test_past_most_recent_first_including_cancelled():
    appts = [
        appt(1, datetime(2025, 12, 1, 9, 0)),
        appt(2, datetime(2026, 2, 1, 9, 0), status="cancelled"),
        appt(3, datetime(2026, 10, 26, 8, 0)),
        appt(4, datetime(2026, 10, 1, 15, 0)),
    ]
    assert ids(past_appointments(appts, NOW)) == [3, 4, 2, 1]


def test_rows_keep_display_time():
    rows = upcoming_appointments([appt(1, datetime(2027, 1, 5, 14, 0))], NOW)
    assert rows[0]["display_time"] == "01/05/2027 02:00 PM"


def test_appointments_endpoint(client, make_patient, make_appointment):
    patient = make_patient()
    make_appointment(patient, datetime(2027, 1, 5, 9, 0))
    make_appointment(patient, datetime(2026, 12, 1, 9, 0))
    make_appointment(patient, datetime(2026, 11, 2, 9, 0), status="cancelled")
    make_appointment(patient, datetime(2026, 9, 1, 9, 0), status="completed")

    response = client.get(f"/patients/{patient.id}/appointments", params={"now": NOW.isoformat()})

    assert response.status_code == 200
    body = response.json()
    assert [a["starts_at"][:10] for a in body["upcoming"]] == ["2026-12-01", "2027-01-05"]
    assert [a["starts_at"][:10] for a in body["past"]] == ["2026-09-01"]
