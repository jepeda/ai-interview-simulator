"""PART 1 (debug) -- open appointment slots.

Bug report (BOOK-198, from the patient app team):
  > A patient in New York looked at Dr. Rivera (a New York provider whose hours are 9am-12pm)
  > and saw slots at 4am, 5am and 6am. A different patient booked a slot that overlapped an
  > existing 10:30 session. Slots also never come back after an appointment is cancelled.
  > And a NY patient looking at a Honolulu-based provider sees nothing at all for some days.

Spec for open_slots:
  1. Availability windows are weekly and expressed in the PROVIDER's timezone (provider.timezone).
  2. Sessions start on the hour (:00) inside a window, last provider.session_minutes, and must END
     no later than the window's end_time.
  3. A slot is unavailable if it OVERLAPS any appointment that isn't cancelled.
     (Intervals [a, b) and [c, d) overlap when a < d and c < b.)
  4. Slots that start before `now` are excluded (a slot starting exactly at `now` is still open).
  5. `day` is a calendar date in the VIEWER's timezone `tz`: return every slot whose start falls on
     that date in `tz` -- even if it comes from the provider's previous or next local day.
     Return them sorted, as aware datetimes in `tz`.
"""

from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from booking.models import Appointment, Provider
from booking.schemas import Slot
from booking.timeutil import from_db

SLOT_STEP = timedelta(hours=1)


def open_slots(
    provider: Provider,
    day: date,
    tz: ZoneInfo,
    appointments: Iterable[Appointment],
    now: datetime,
) -> list[Slot]:
    length = timedelta(minutes=provider.session_minutes)
    booked_starts = {from_db(a.starts_at) for a in appointments}

    slots: list[Slot] = []
    for window in provider.availability:
        if window.weekday != day.weekday():
            continue
        start = datetime.combine(day, window.start_time, tzinfo=UTC)
        window_end = datetime.combine(day, window.end_time, tzinfo=UTC)
        while start + length <= window_end:
            if start not in booked_starts and start >= now:
                slots.append(Slot(starts_at=start.astimezone(tz), ends_at=(start + length).astimezone(tz)))
            start += SLOT_STEP

    return sorted(slots, key=lambda s: s.starts_at)
