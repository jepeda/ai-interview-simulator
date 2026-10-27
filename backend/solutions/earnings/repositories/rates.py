from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from earnings.models import ContractedRate


def list_for_provider(db: Session, provider_id: int) -> list[ContractedRate]:
    """Every fee-schedule entry for a provider, in the order ops entered them (the audit trail)."""
    stmt = (
        select(ContractedRate)
        .where(ContractedRate.provider_id == provider_id)
        .order_by(ContractedRate.created_at, ContractedRate.id)
    )
    return list(db.scalars(stmt))


def contracted_codes(db: Session, provider_id: int) -> list[tuple[str, str]]:
    """Distinct (payer, cpt_code) pairs the provider has rates for, alphabetically."""
    stmt = (
        select(ContractedRate.payer, ContractedRate.cpt_code)
        .where(ContractedRate.provider_id == provider_id)
        .distinct()
        .order_by(ContractedRate.payer, ContractedRate.cpt_code)
    )
    return [(payer, cpt) for payer, cpt in db.execute(stmt)]


def in_effect(db: Session, provider_id: int, payer: str, cpt_code: str, day: date) -> ContractedRate | None:
    """The entry that applies on `day`: latest effective date on or before it, newest entry first."""
    stmt = (
        select(ContractedRate)
        .where(
            ContractedRate.provider_id == provider_id,
            ContractedRate.payer == payer,
            ContractedRate.cpt_code == cpt_code,
            ContractedRate.effective_date <= day,
        )
        .order_by(ContractedRate.effective_date.desc(), ContractedRate.created_at.desc(), ContractedRate.id.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def next_change(db: Session, provider_id: int, payer: str, cpt_code: str, after: date) -> ContractedRate | None:
    """The first entry that takes effect after `after` (a scheduled rate change), if any."""
    stmt = (
        select(ContractedRate)
        .where(
            ContractedRate.provider_id == provider_id,
            ContractedRate.payer == payer,
            ContractedRate.cpt_code == cpt_code,
            ContractedRate.effective_date > after,
        )
        .order_by(ContractedRate.effective_date, ContractedRate.created_at.desc(), ContractedRate.id.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def get_for_provider(db: Session, provider_id: int, rate_id: int) -> ContractedRate | None:
    entry = db.get(ContractedRate, rate_id)
    return entry if entry is not None and entry.provider_id == provider_id else None
