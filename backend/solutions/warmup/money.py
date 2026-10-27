"""Cents helpers. Money is integer cents in the backend."""


def percent_of(cents: int, pct: int) -> int:
    """`pct` percent of an amount in cents, to the nearest cent; half a cent rounds up (Finance policy).

    Integer math: no float error, and no banker's rounding like round()."""
    return (cents * pct + 50) // 100
