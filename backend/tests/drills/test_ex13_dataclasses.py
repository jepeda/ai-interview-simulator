from dataclasses import FrozenInstanceError, asdict
from datetime import datetime

import pytest

from drills.ex13_dataclasses import Appointment, AppointmentStatus, Claim, PlanKey, cancel

START = datetime(2026, 10, 26, 9, 0)


def test_appointment_defaults():
    appt = Appointment(provider="Dr. Lee", starts_at=START)
    assert appt.duration_minutes == 50
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.tags == []


def test_appointment_tags_not_shared():
    a = Appointment(provider="Dr. Lee", starts_at=START)
    b = Appointment(provider="Dr. Ng", starts_at=START)
    a.tags.append("intake")
    assert b.tags == []


def test_appointment_ends_at_property():
    appt = Appointment(provider="Dr. Lee", starts_at=START, duration_minutes=90)
    assert appt.ends_at == datetime(2026, 10, 26, 10, 30)


def test_status_is_enum_and_compares_to_string():
    appt = Appointment(provider="Dr. Lee", starts_at=START)
    assert isinstance(appt.status, AppointmentStatus)
    assert appt.status == "scheduled"


def test_plan_key_is_frozen_and_hashable():
    key = PlanKey("Aetna", "PPO-1")
    assert key == PlanKey("Aetna", "PPO-1")
    assert len({key, PlanKey("Aetna", "PPO-1"), PlanKey("Cigna", "HMO")}) == 2
    with pytest.raises(FrozenInstanceError):
        key.payer = "Other"  # type: ignore[misc]


def test_claim_validation():
    assert Claim(patient_id=1, amount_cents=0).amount_cents == 0
    with pytest.raises(ValueError):
        Claim(patient_id=1, amount_cents=-1)


def test_claim_status_not_in_init():
    claim = Claim(patient_id=1, amount_cents=500)
    assert claim.status == "submitted"
    with pytest.raises(TypeError):
        Claim(patient_id=1, amount_cents=500, status="paid")  # type: ignore[call-arg]


def test_claim_asdict():
    assert asdict(Claim(patient_id=1, amount_cents=500)) == {
        "patient_id": 1,
        "amount_cents": 500,
        "status": "submitted",
    }


def test_cancel_returns_copy():
    appt = Appointment(provider="Dr. Lee", starts_at=START)
    cancelled = cancel(appt)
    assert cancelled.status == AppointmentStatus.CANCELLED
    assert appt.status == AppointmentStatus.SCHEDULED
    assert cancelled is not appt
