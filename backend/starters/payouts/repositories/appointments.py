from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from payouts.models import Appointment


def list_between(db: Session, provider_id: int, start: datetime, end: datetime) -> list[Appointment]:
    """A provider's appointments with start <= starts_at < end.

    `start` and `end` are naive UTC, like the column (see timeutil.py).
    """
    stmt = (
        select(Appointment)
        .where(
            Appointment.provider_id == provider_id,
            Appointment.starts_at >= start,
            Appointment.starts_at < end,
        )
        .order_by(Appointment.starts_at, Appointment.id)
    )
    return list(db.scalars(stmt))


def list_for_provider(db: Session, provider_id: int) -> list[Appointment]:
    stmt = (
        select(Appointment)
        .where(Appointment.provider_id == provider_id)
        .order_by(Appointment.starts_at, Appointment.id)
    )
    return list(db.scalars(stmt))
