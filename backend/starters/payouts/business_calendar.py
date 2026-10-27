"""Acme Health's business calendar (owned by Finance). Payouts are only sent on business days."""

from datetime import date

# Bank holidays on which Acme Health does not send payouts.
ACME_HOLIDAYS: frozenset[date] = frozenset(
    {
        date(2026, 9, 7),  # Labor Day
        date(2026, 10, 12),  # Columbus Day (banks closed)
        date(2026, 11, 11),  # Veterans Day (banks closed)
        date(2026, 11, 26),  # Thanksgiving
        date(2026, 12, 25),  # Christmas
        date(2027, 1, 1),  # New Year's Day
        date(2027, 1, 18),  # MLK Day
    }
)
