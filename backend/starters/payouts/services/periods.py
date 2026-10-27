"""Pay periods: semi-monthly, the 1st-15th and the 16th-last day of the month.

Finance policy: periods are calendar days in the PROVIDER'S timezone. A session belongs to the
period containing its local date of service.
"""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from payouts.errors import InvalidRequest
from payouts.models import Appointment


@dataclass(frozen=True, order=True)
class PayPeriod:
    start: date
    end: date  # inclusive

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end

    def next(self) -> "PayPeriod":
        return period_containing(self.end + timedelta(days=1))

    def previous(self) -> "PayPeriod":
        return period_containing(self.start - timedelta(days=1))


def period_containing(day: date) -> PayPeriod:
    if day.day <= 15:
        return PayPeriod(day.replace(day=1), day.replace(day=15))
    last = calendar.monthrange(day.year, day.month)[1]
    return PayPeriod(day.replace(day=16), day.replace(day=last))


def period_starting(start: date) -> PayPeriod:
    """The period that starts on `start` (from a URL). Must be the 1st or the 16th."""
    if start.day not in (1, 16):
        raise InvalidRequest(
            f"{start.isoformat()} is not the start of a pay period (use the 1st or the 16th)",
            code="invalid_period",
        )
    return period_containing(start)


def query_bounds(period: PayPeriod) -> tuple[datetime, datetime]:
    """[start, end) of the period as naive datetimes, for querying Appointment.starts_at."""
    start = datetime.combine(period.start, time.min)
    end = datetime.combine(period.end + timedelta(days=1), time.min)
    return start, end


def period_of(appointment: Appointment) -> PayPeriod:
    """The pay period an appointment is paid in."""
    return period_containing(appointment.starts_at.date())
