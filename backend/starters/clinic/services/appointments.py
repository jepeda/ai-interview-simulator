"""Appointment views shown on the patient detail page."""

from collections.abc import Iterable
from datetime import datetime

from clinic.models import Appointment

DISPLAY_FORMAT = "%m/%d/%Y %I:%M %p"  # e.g. "01/05/2027 02:00 PM"


def to_row(appt: Appointment) -> dict:
    return {
        "id": appt.id,
        "provider_name": appt.provider_name,
        "starts_at": appt.starts_at,
        "duration_minutes": appt.duration_minutes,
        "status": appt.status,
        "display_time": appt.starts_at.strftime(DISPLAY_FORMAT),
    }


def upcoming_appointments(appointments: Iterable[Appointment], now: datetime) -> list[dict]:
    """Appointments starting at or after `now` that are NOT cancelled, soonest first."""
    rows = [to_row(a) for a in appointments if a.starts_at >= now]
    return sorted(rows, key=lambda row: row["display_time"])


def past_appointments(appointments: Iterable[Appointment], now: datetime) -> list[dict]:
    """Appointments that started before `now` (any status), most recent first."""
    rows = [to_row(a) for a in appointments if a.starts_at < now]
    return sorted(rows, key=lambda row: row["display_time"], reverse=True)
