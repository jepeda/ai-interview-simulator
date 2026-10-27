from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from booking.errors import NotFound
from booking.models import Appointment


def get_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise NotFound(f"Appointment {appointment_id} not found")
    return appointment


def get_by_idempotency_key(db: Session, key: str) -> Appointment | None:
    return db.scalar(select(Appointment).where(Appointment.idempotency_key == key))


def list_for_provider(
    db: Session, provider_id: int, start_utc: datetime, end_utc: datetime
) -> list[Appointment]:
    """Appointments of ANY status that overlap [start_utc, end_utc). Arguments are naive UTC (DB format)."""
    stmt = (
        select(Appointment)
        .where(
            Appointment.provider_id == provider_id,
            Appointment.starts_at < end_utc,
            Appointment.ends_at > start_utc,
        )
        .order_by(Appointment.starts_at)
    )
    return list(db.scalars(stmt).all())
