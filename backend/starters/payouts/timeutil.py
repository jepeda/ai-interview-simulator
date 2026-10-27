"""Timezone helpers. Read this before touching anything with dates.

Rules of the codebase:
  * In Python, work with AWARE datetimes (tzinfo set). Comparing aware datetimes compares instants,
    even across timezones: 18:30-07:00 == 01:30+00:00 the next day.
  * In the database, store NAIVE UTC (SQLite has no timezone type). Convert with to_db / from_db.
  * Every provider has an IANA timezone (Provider.timezone). Anything a provider sees as a
    "day" -- a session's date of service, a pay period, an adjustment's effective date -- is a
    day in THAT timezone, not in UTC. (Finance policy: see README "Pay periods".)
  * datetime.combine(day, time.min, tzinfo=zone("America/Los_Angeles")) is local midnight on that
    day, with the right DST offset (PDT -07:00 in summer, PST -08:00 in winter).
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from payouts.errors import InvalidRequest


def to_db(value: datetime) -> datetime:
    """Aware datetime -> naive UTC for storage."""
    if value.tzinfo is None:
        raise ValueError("to_db() needs an aware datetime")
    return value.astimezone(UTC).replace(tzinfo=None)


def from_db(value: datetime) -> datetime:
    """Naive UTC from the database -> aware UTC."""
    return value.replace(tzinfo=UTC)


def zone(name: str) -> ZoneInfo:
    """Look up an IANA timezone ("America/Los_Angeles"); unknown names are a 422."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as err:
        raise InvalidRequest(f"Unknown timezone {name!r}", code="invalid_timezone") from err
