"""Appointment views (reference solution).

Fixes:
  - sort by the real datetime (starts_at), never by a formatted display string
  - exclude cancelled appointments from the upcoming list
"""

from collections.abc import Iterable
from datetime import datetime

from clinic.models import Appointment

DISPLAY_FORMAT = "%m/%d/%Y %I:%M %p"


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
    upcoming = sorted(
        (a for a in appointments if a.starts_at >= now and a.status != "cancelled"),
        key=lambda a: a.starts_at,
    )
    return [to_row(a) for a in upcoming]


def past_appointments(appointments: Iterable[Appointment], now: datetime) -> list[dict]:
    past = sorted((a for a in appointments if a.starts_at < now), key=lambda a: a.starts_at, reverse=True)
    return [to_row(a) for a in past]
