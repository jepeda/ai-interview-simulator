"""When Acme Health sends a period's payout: 5 business days after the period ends."""

from datetime import date, timedelta

from payouts.business_calendar import ACME_HOLIDAYS

BUSINESS_DAYS_AFTER_PERIOD_END = 5


def is_business_day(day: date) -> bool:
    return day.weekday() < 5 and day not in ACME_HOLIDAYS


def expected_pay_date(period_end: date) -> date:
    day, remaining = period_end, BUSINESS_DAYS_AFTER_PERIOD_END
    while remaining:
        day += timedelta(days=1)
        if is_business_day(day):
            remaining -= 1
    return day
