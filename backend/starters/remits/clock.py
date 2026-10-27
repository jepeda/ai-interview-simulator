"""Clock dependencies, so tests can pin "now" and "today" (override them in app.dependency_overrides)."""

from datetime import UTC, date, datetime


def get_now() -> datetime:
    """Aware UTC."""
    return datetime.now(UTC)


def get_today() -> date:
    """Today's business date."""
    return date.today()
