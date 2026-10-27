from datetime import date, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from booking.models import Appointment, Provider
from booking.timeutil import from_db


class ProviderSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    credential: str
    timezone: str
    accepting_new_patients: bool
    rating: float | None
    session_minutes: int
    session_rate_cents: int
    states: list[str]
    payers: list[str]
    specialties: list[str]

    @classmethod
    def from_model(cls, p: Provider) -> "ProviderSummary":
        return cls(
            id=p.id,
            first_name=p.first_name,
            last_name=p.last_name,
            credential=p.credential,
            timezone=p.timezone,
            accepting_new_patients=p.accepting_new_patients,
            rating=p.rating,
            session_minutes=p.session_minutes,
            session_rate_cents=p.session_rate_cents,
            states=sorted({lic.state for lic in p.licenses}),
            payers=sorted(pp.payer_name for pp in p.payers),
            specialties=sorted(s.slug for s in p.specialties),
        )


class ProviderPage(BaseModel):
    items: list[ProviderSummary]
    total: int
    page: int
    page_size: int


class Slot(BaseModel):
    starts_at: datetime  # aware, in the requested timezone
    ends_at: datetime


class SlotsOut(BaseModel):
    provider_id: int
    date: date
    timezone: str
    slots: list[Slot]


class BookingRequest(BaseModel):
    provider_id: int
    patient_id: int
    starts_at: AwareDatetime  # must include an offset, e.g. "2026-11-02T09:00:00-05:00"
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=100)


class CancelRequest(BaseModel):
    cancelled_by: Literal["patient", "provider"]
    reason: str = Field(default="", max_length=500)


class AppointmentOut(BaseModel):
    id: int
    provider_id: int
    patient_id: int
    starts_at: datetime  # aware UTC
    ends_at: datetime
    status: str
    idempotency_key: str | None
    cancelled_at: datetime | None
    cancelled_by: str | None
    cancel_reason: str | None
    late_cancel_fee_cents: int

    @classmethod
    def from_model(cls, a: Appointment) -> "AppointmentOut":
        return cls(
            id=a.id,
            provider_id=a.provider_id,
            patient_id=a.patient_id,
            starts_at=from_db(a.starts_at),
            ends_at=from_db(a.ends_at),
            status=a.status,
            idempotency_key=a.idempotency_key,
            cancelled_at=from_db(a.cancelled_at) if a.cancelled_at else None,
            cancelled_by=a.cancelled_by,
            cancel_reason=a.cancel_reason,
            late_cancel_fee_cents=a.late_cancel_fee_cents,
        )
