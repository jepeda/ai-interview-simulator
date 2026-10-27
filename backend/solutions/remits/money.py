"""Money helpers.

Everything inside the service (DB columns, API responses) is integer cents. Payers send dollar
amounts as decimal strings, the way they appear in the 835 ("137.17", "-42.15", "25"); convert
them once, at the edge, with to_cents.
"""

from decimal import ROUND_HALF_UP, Decimal

# Up to two decimal places, optional leading minus: "137.17", "-42.15", "25", "0.5"
AMOUNT_PATTERN = r"^-?\d+(\.\d{1,2})?$"


def to_cents(amount: str) -> int:
    """Dollar string from a remittance -> integer cents, exactly.

    Never go through float: float("137.17") * 100 is 13716.999999999998, and int() truncates it to
    13716. Decimal parses the string exactly.
    """
    cents = (Decimal(amount) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(cents)
