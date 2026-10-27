"""Drill 13 - Dataclasses and Enums (reference solution)."""

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Appointment:
    provider: str
    starts_at: datetime
    duration_minutes: int = 50
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    tags: list[str] = field(default_factory=list)

    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(minutes=self.duration_minutes)


@dataclass(frozen=True)
class PlanKey:
    payer: str
    plan_code: str


@dataclass
class Claim:
    patient_id: int
    amount_cents: int
    status: str = field(default="submitted", init=False)

    def __post_init__(self) -> None:
        if self.amount_cents < 0:
            raise ValueError("amount_cents must be >= 0")


def cancel(appointment: Appointment) -> Appointment:
    return replace(appointment, status=AppointmentStatus.CANCELLED)
