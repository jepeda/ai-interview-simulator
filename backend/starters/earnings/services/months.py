"""Calendar months, as the API addresses them: "2026-07"."""

import calendar
import re
from dataclasses import dataclass
from datetime import date

from earnings.errors import InvalidRequest

_MONTH = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True, order=True)
class Month:
    year: int
    month: int

    @property
    def first_day(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        return date(self.year, self.month, calendar.monthrange(self.year, self.month)[1])

    def key(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


def month_of(day: date) -> Month:
    return Month(day.year, day.month)


def parse_month(raw: str) -> Month:
    """"2026-07" -> Month(2026, 7). Anything else is a 422."""
    match = _MONTH.match(raw)
    if match is None or not 1 <= int(match.group(2)) <= 12:
        raise InvalidRequest(f"{raw!r} is not a month (use YYYY-MM)", code="invalid_month")
    return Month(int(match.group(1)), int(match.group(2)))
