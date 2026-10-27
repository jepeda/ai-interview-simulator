"""Drill 11 - Custom exceptions and context managers (reference solution)."""

from contextlib import contextmanager


class ClinicError(Exception):
    """Base class for all clinic domain errors."""


class EligibilityError(ClinicError):
    def __init__(self, patient_id: int, reason: str) -> None:
        super().__init__(f"Patient {patient_id} is not eligible: {reason}")
        self.patient_id = patient_id
        self.reason = reason


def require_eligible(patient: dict) -> None:
    if not patient["eligible"]:
        raise EligibilityError(patient["id"], patient["reason"])


@contextmanager
def audit(events: list[str], action: str):
    events.append(f"start:{action}")
    try:
        yield
    except BaseException:
        events.append(f"error:{action}")
        raise
    events.append(f"ok:{action}")


class StagedChanges:
    def __init__(self, target: list[str]) -> None:
        self.target = target
        self.staged: list[str] = []

    def __enter__(self) -> list[str]:
        return self.staged

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self.target.extend(self.staged)
        return False  # never swallow exceptions
