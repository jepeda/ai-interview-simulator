"""Money helpers.

Everything inside the service (DB columns, API responses) is integer cents. Payers send dollar
amounts as decimal strings, the way they appear in the 835 ("137.17", "-42.15", "25"); convert
them once, at the edge, with to_cents.
"""

# Up to two decimal places, optional leading minus: "137.17", "-42.15", "25", "0.5"
AMOUNT_PATTERN = r"^-?\d+(\.\d{1,2})?$"


def to_cents(amount: str) -> int:
    """Dollar string from a remittance -> integer cents."""
    dollars = float(amount)
    return int(dollars * 100)
