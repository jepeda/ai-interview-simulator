"""Timezone helpers. Read this before touching anything with dates.

Rules of the codebase:
  * In Python, work with AWARE datetimes (tzinfo set). Comparing aware datetimes compares instants,
    even across different timezones: 09:00-05:00 == 14:00+00:00.
  * In the database, store NAIVE UTC (SQLite has no timezone type). Convert with to_db / from_db.
  * Providers' weekly availability is in the provider's own IANA timezone (Provider.timezone).
  * datetime.combine(day, time(9, 0), tzinfo=zone("America/New_York")) gives 09:00 New York time on
    that day, with the correct DST offset (EDT -04:00 in summer, EST -05:00 in winter).
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from booking.errors import InvalidRequest


def to_db(value: datetime) -> datetime:
    """Aware datetime -> naive UTC for storage."""
    if value.tzinfo is None:
        raise ValueError("to_db() needs an aware datetime")
    return value.astimezone(UTC).replace(tzinfo=None)


def from_db(value: datetime) -> datetime:
    """Naive UTC from the database -> aware UTC."""
    return value.replace(tzinfo=UTC)


def zone(name: str) -> ZoneInfo:
    """Look up an IANA timezone ("America/New_York"); unknown names are a 422."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as err:
        raise InvalidRequest(f"Unknown timezone {name!r}", code="invalid_timezone") from err
