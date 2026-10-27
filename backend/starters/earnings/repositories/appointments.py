from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from earnings.models import Appointment


def list_between(db: Session, provider_id: int, first_day: date, last_day: date) -> list[Appointment]:
    """A provider's appointments with service_date in [first_day, last_day] (both inclusive)."""
    stmt = (
        select(Appointment)
        .where(
            Appointment.provider_id == provider_id,
            Appointment.service_date >= first_day,
            Appointment.service_date <= last_day,
        )
        .order_by(Appointment.service_date, Appointment.start_time, Appointment.id)
    )
    return list(db.scalars(stmt))
