from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from payouts.models import Adjustment


def list_between(db: Session, provider_id: int, first_day: date, last_day: date) -> list[Adjustment]:
    """Adjustments whose effective_date is in [first_day, last_day] (both inclusive)."""
    stmt = (
        select(Adjustment)
        .where(
            Adjustment.provider_id == provider_id,
            Adjustment.effective_date >= first_day,
            Adjustment.effective_date <= last_day,
        )
        .order_by(Adjustment.effective_date, Adjustment.id)
    )
    return list(db.scalars(stmt))


def list_for_provider(db: Session, provider_id: int) -> list[Adjustment]:
    stmt = (
        select(Adjustment)
        .where(Adjustment.provider_id == provider_id)
        .order_by(Adjustment.effective_date, Adjustment.id)
    )
    return list(db.scalars(stmt))
