"""The current time, as a FastAPI dependency.

Services receive `now` as an argument instead of calling datetime.now(), so tests can freeze time
with `app.dependency_overrides[get_now] = lambda: some_datetime`.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends


def get_now() -> datetime:
    """Current time, timezone-aware, in UTC."""
    return datetime.now(UTC)


Now = Annotated[datetime, Depends(get_now)]
