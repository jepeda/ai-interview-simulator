"""Datetime helpers. In Python use AWARE datetimes; the DB stores NAIVE UTC (SQLite has no tz type)."""

from datetime import UTC, datetime


def to_db(value: datetime) -> datetime:
    """Aware datetime -> naive UTC for storage."""
    if value.tzinfo is None:
        raise ValueError("to_db() needs an aware datetime")
    return value.astimezone(UTC).replace(tzinfo=None)


def from_db(value: datetime) -> datetime:
    """Naive UTC from the database -> aware UTC."""
    return value.replace(tzinfo=UTC)
