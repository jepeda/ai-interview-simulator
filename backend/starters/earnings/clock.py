"""Today's date, as a FastAPI dependency.

Services receive `today` as an argument instead of calling date.today(), so tests can freeze it
with `app.dependency_overrides[get_today] = lambda: date(2026, 10, 23)`.

Acme Health's provider-payments calendar runs on US Eastern time, so "today" is the Eastern date.
"""

from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends

ACME_TZ = ZoneInfo("America/New_York")


def get_today() -> date:
    return datetime.now(ACME_TZ).date()


Today = Annotated[date, Depends(get_today)]
