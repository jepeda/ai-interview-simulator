"""Drill 10 - Exceptions (reference solution)."""

from decimal import Decimal, InvalidOperation


class PatientNotFoundError(Exception):
    """Raised when a patient id does not exist."""


def parse_copay(raw: str) -> int:
    cleaned = raw.strip().removeprefix("$").replace(",", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as err:
        raise ValueError(f"Invalid copay: {raw!r}") from err
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise ValueError(f"Invalid copay: {raw!r}")
    return int(amount * 100)


def safe_parse_copay(raw: str) -> int | None:
    try:
        return parse_copay(raw)
    except ValueError:
        return None


def load_patient(store: dict[int, dict], patient_id: int) -> dict:
    try:
        return store[patient_id]
    except KeyError as err:
        raise PatientNotFoundError(f"Patient {patient_id} not found") from err


def parse_batch(raws: list[str]) -> tuple[list[int], list[str]]:
    parsed: list[int] = []
    errors: list[str] = []
    for raw in raws:
        try:
            parsed.append(parse_copay(raw))
        except ValueError as err:
            errors.append(str(err))
    return parsed, errors
