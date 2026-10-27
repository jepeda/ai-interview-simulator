"""PARTS 3 & 4 -- booking and cancelling (reference solution)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from booking.errors import (
    IdempotencyKeyReused,
    InvalidTransition,
    NotLicensedInState,
    PayerNotAccepted,
    SlotUnavailable,
)
from booking.models import Appointment
from booking.repositories import appointments as appointments_repo
from booking.repositories import providers as providers_repo
from booking.schemas import BookingRequest, CancelRequest
from booking.services.availability import open_slots
from booking.timeutil import from_db, to_db, zone

LATE_CANCEL_WINDOW = timedelta(hours=24)


def book_appointment(db: Session, request: BookingRequest, now: datetime) -> tuple[Appointment, bool]:
    starts_at = request.starts_at.astimezone(UTC)

    if request.idempotency_key:
        existing = appointments_repo.get_by_idempotency_key(db, request.idempotency_key)
        if existing is not None:
            same_request = (
                existing.provider_id == request.provider_id
                and existing.patient_id == request.patient_id
                and from_db(existing.starts_at) == starts_at
            )
            if not same_request:
                raise IdempotencyKeyReused("Idempotency key was already used for a different booking")
            return existing, False

    provider = providers_repo.get_provider(db, request.provider_id)
    patient = providers_repo.get_patient(db, request.patient_id)

    if not any(lic.state == patient.state and lic.expires_on >= now.date() for lic in provider.licenses):
        raise NotLicensedInState(f"Provider {provider.id} is not licensed in {patient.state}")

    if patient.payer_name is not None:
        accepted = {pp.payer_name.lower() for pp in provider.payers}
        if patient.payer_name.lower() not in accepted:
            raise PayerNotAccepted(f"Provider {provider.id} is not in-network with {patient.payer_name}")

    provider_tz = zone(provider.timezone)
    local_day = starts_at.astimezone(provider_tz).date()
    booked = appointments_repo.list_for_provider(
        db, provider.id, to_db(starts_at - timedelta(days=2)), to_db(starts_at + timedelta(days=2))
    )
    slots = open_slots(provider, local_day, provider_tz, booked, now)
    if not any(slot.starts_at == starts_at for slot in slots):
        raise SlotUnavailable("That time is not available")

    appointment = Appointment(
        provider_id=provider.id,
        patient_id=patient.id,
        starts_at=to_db(starts_at),
        ends_at=to_db(starts_at + timedelta(minutes=provider.session_minutes)),
        status="booked",
        idempotency_key=request.idempotency_key,
        created_at=to_db(now),
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment, True


def cancel_appointment(
    db: Session, appointment_id: int, request: CancelRequest, now: datetime
) -> Appointment:
    appointment = appointments_repo.get_appointment(db, appointment_id)
    if appointment.status != "booked":
        raise InvalidTransition(f"Cannot cancel an appointment that is {appointment.status}")

    starts_at = from_db(appointment.starts_at)
    if starts_at <= now:
        raise InvalidTransition("Cannot cancel an appointment that has already started")

    fee = 0
    if request.cancelled_by == "patient" and starts_at - now < LATE_CANCEL_WINDOW:
        fee = (appointment.provider.session_rate_cents + 1) // 2  # 50%, half a cent rounds up

    appointment.status = "cancelled"
    appointment.cancelled_at = to_db(now)
    appointment.cancelled_by = request.cancelled_by
    appointment.cancel_reason = request.reason
    appointment.late_cancel_fee_cents = fee
    db.commit()
    db.refresh(appointment)
    return appointment
