"""PART 1 -- open appointment slots (reference solution).

Fixes:
  1. Windows were built in UTC; build them in the provider's timezone.
  2. Only the provider's local day == `day` was scanned; scan the neighbouring days too and keep the
     slots whose start falls on `day` in the viewer's timezone (e.g. a Honolulu evening is the next
     morning in New York).
  3. Booked-ness was "same start time"; use interval overlap.
  4. Cancelled appointments blocked slots; ignore them.
"""

from collections.abc import Iterable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from booking.models import Appointment, Provider
from booking.schemas import Slot
from booking.timeutil import from_db, zone

SLOT_STEP = timedelta(hours=1)


def open_slots(
    provider: Provider,
    day: date,
    tz: ZoneInfo,
    appointments: Iterable[Appointment],
    now: datetime,
) -> list[Slot]:
    provider_tz = zone(provider.timezone)
    length = timedelta(minutes=provider.session_minutes)
    busy = [
        (from_db(a.starts_at), from_db(a.ends_at)) for a in appointments if a.status != "cancelled"
    ]

    slots: list[Slot] = []
    for offset in (-1, 0, 1):
        local_day = day + timedelta(days=offset)
        for window in provider.availability:
            if window.weekday != local_day.weekday():
                continue
            start = datetime.combine(local_day, window.start_time, tzinfo=provider_tz)
            window_end = datetime.combine(local_day, window.end_time, tzinfo=provider_tz)
            while start + length <= window_end:
                end = start + length
                overlaps = any(b_start < end and start < b_end for b_start, b_end in busy)
                if start.astimezone(tz).date() == day and start >= now and not overlaps:
                    slots.append(Slot(starts_at=start.astimezone(tz), ends_at=end.astimezone(tz)))
                start += SLOT_STEP

    return sorted(slots, key=lambda s: s.starts_at)
