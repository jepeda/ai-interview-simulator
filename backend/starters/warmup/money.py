"""Cents helpers. Money is integer cents in the backend."""


def percent_of(cents: int, pct: int) -> int:
    """`pct` percent of an amount in cents."""
    return int(cents * pct / 100)
