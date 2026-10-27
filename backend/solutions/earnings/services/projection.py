"""Month-end projection: earned so far plus booked sessions still to come, at their own dates' rates."""

from datetime import date

from sqlalchemy.orm import Session

from earnings.models import Provider, SessionStatus
from earnings.repositories import appointments as appointments_repo
from earnings.schemas import Projection
from earnings.services.months import Month
from earnings.services.rates import load_rate_table


def project_month(db: Session, provider: Provider, month: Month, today: date) -> Projection:
    rates = load_rate_table(db, provider.id)
    earned = projected = completed = scheduled = undocumented = 0
    for appt in appointments_repo.list_between(db, provider.id, month.first_day, month.last_day):
        if appt.status == SessionStatus.COMPLETED:
            completed += 1
            earned += rates.rate_for(appt)
        elif appt.status == SessionStatus.SCHEDULED:
            if appt.service_date < today:
                undocumented += 1  # booked in the past but never documented: don't count it
            else:
                scheduled += 1
                projected += rates.rate_for(appt)
    return Projection(
        provider_id=provider.id,
        month=month.key(),
        earned_cents=earned,
        projected_cents=projected,
        total_cents=earned + projected,
        completed_count=completed,
        scheduled_count=scheduled,
        undocumented_count=undocumented,
    )
