"""Drill 13 - Dataclasses and Enums.

TS mental model: a dataclass is like a TS `interface` + auto-generated constructor,
equality and repr. (Pydantic models, used by FastAPI, look similar but also VALIDATE input.)
`class Status(StrEnum): ACTIVE = "active"` is like a TS string enum; Status("active") parses.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen dataclasses/enums cheat sheet.
Right now this module doesn't even import: read that error message first.
"""

from dataclasses import dataclass, field  # noqa: F401
from datetime import datetime, timedelta
from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ── Q1 · Appointment ─────────────────────────────────────────── fix the bug ──
# One booked visit on a provider's calendar. Only provider and starts_at are
# required; everything else has a default.
#
#   appt = Appointment(provider="Dr. Lee", starts_at=datetime(2026, 10, 26, 9, 0))
#   appt.duration_minutes        -> 50
#   appt.status                  -> AppointmentStatus.SCHEDULED   an enum member...
#   appt.status == "scheduled"   -> True                          ...that still equals the string
#   appt.tags                    -> []
#
# - every Appointment gets its OWN tags list: appending "intake" to one
#   appointment's tags must leave another appointment's tags == []
# - ends_at is a read-only property (no parentheses): starts_at + duration
#     Appointment("Dr. Lee", datetime(2026, 10, 26, 9, 0), duration_minutes=90).ends_at
#         -> datetime(2026, 10, 26, 10, 30)
#
# Today: the whole module fails to import with a ValueError from dataclasses
# about the `tags` default. Once that's fixed, status is a plain str and
# appt.ends_at is a bound method, not a datetime.
@dataclass
class Appointment:
    provider: str
    starts_at: datetime
    duration_minutes: int = 50
    status: str = "scheduled"
    tags: list[str] = []

    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(minutes=self.duration_minutes)


# ── Q2 · PlanKey ─────────────────────────────────────────────── fix the bug ──
# Identifies an insurance plan: (payer, plan_code). Used as a dict key and in
# sets, so it must be hashable, and immutable so a key can't change under you.
#
#   PlanKey("Aetna", "PPO-1") == PlanKey("Aetna", "PPO-1")    -> True
#   len({PlanKey("Aetna", "PPO-1"), PlanKey("Aetna", "PPO-1"),
#        PlanKey("Cigna", "HMO")})                             -> 2
#   key.payer = "Other"   -> raises dataclasses.FrozenInstanceError
#
# Today: putting a PlanKey in a set raises TypeError (unhashable), and
# assigning to a field silently works.
@dataclass
class PlanKey:
    payer: str
    plan_code: str


# ── Q3 · Claim ───────────────────────────────────────────────── fix the bug ──
# A billing claim sent to a payer.
#
# - amount_cents must be >= 0: a negative amount raises ValueError the moment
#   the Claim is constructed. 0 is allowed.
# - status is NOT a constructor argument: every claim starts as "submitted",
#   and passing status=... raises TypeError. It is still a real dataclass
#   field, so it shows up in asdict().
#
#   Claim(patient_id=1, amount_cents=0).amount_cents            -> 0
#   Claim(patient_id=1, amount_cents=-1)                        -> raises ValueError
#   Claim(patient_id=1, amount_cents=500).status                -> "submitted"
#   Claim(patient_id=1, amount_cents=500, status="paid")        -> raises TypeError
#   asdict(Claim(patient_id=1, amount_cents=500))
#       -> {"patient_id": 1, "amount_cents": 500, "status": "submitted"}
#
# Today: negative amounts are accepted and callers can pass any status.
@dataclass
class Claim:
    patient_id: int
    amount_cents: int
    status: str = "submitted"


# ── Q4 · cancel ──────────────────────────────────────────────── fix the bug ──
# The patient cancels. Return a NEW Appointment identical to `appointment`
# except status == AppointmentStatus.CANCELLED. The original must be untouched:
# other code still holds a reference to it.
#
#   cancelled = cancel(appt)
#   cancelled.status    -> AppointmentStatus.CANCELLED
#   appt.status         -> AppointmentStatus.SCHEDULED   unchanged
#   cancelled is appt   -> False
#
# Today: it mutates the original and returns that same object.
# TS equivalent: `return { ...appointment, status: "cancelled" }`
def cancel(appointment: Appointment) -> Appointment:
    appointment.status = "cancelled"
    return appointment
