"""Network Ops schedules future rate changes; a scheduled change can be cancelled until it takes effect."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from earnings.errors import Conflict, InvalidRequest, NotFound
from earnings.models import ContractedRate, Provider
from earnings.repositories import rates as rates_repo
from earnings.schemas import RateChangeIn


def schedule_rate_change(
    db: Session, provider: Provider, change: RateChangeIn, today: date, entered_at: datetime
) -> ContractedRate:
    if change.effective_date <= today:
        raise InvalidRequest(
            f"Rate changes must take effect after today ({today.isoformat()})",
            code="effective_date_not_in_future",
        )
    pending = rates_repo.next_change(db, provider.id, change.payer, change.cpt_code, today)
    if pending is not None:
        raise Conflict(
            f"{change.payer} {change.cpt_code} already has a change scheduled for "
            f"{pending.effective_date.isoformat()} (rate {pending.id}); cancel it first",
            code="rate_change_conflict",
        )
    entry = ContractedRate(
        provider_id=provider.id,
        payer=change.payer,
        cpt_code=change.cpt_code,
        rate_cents=change.rate_cents,
        effective_date=change.effective_date,
        created_at=entered_at,
        note=change.note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def cancel_rate_change(db: Session, provider: Provider, rate_id: int, today: date) -> None:
    entry = rates_repo.get_for_provider(db, provider.id, rate_id)
    if entry is None:
        raise NotFound(f"Rate {rate_id} not found for provider {provider.id}", code="rate_not_found")
    if entry.effective_date <= today:
        raise Conflict(
            f"Rate {rate_id} took effect on {entry.effective_date.isoformat()}: it's part of the audit "
            "trail now (enter a correction instead)",
            code="rate_in_effect",
        )
    db.delete(entry)
    db.commit()
