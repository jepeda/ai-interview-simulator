"""The provider's rate card: what each (payer, CPT) pays today, and what's scheduled next."""

from datetime import date

from sqlalchemy.orm import Session

from earnings.models import ContractedRate, Provider
from earnings.repositories import rates as rates_repo
from earnings.schemas import RateCardRow, RateChange


def _change(entry: ContractedRate | None) -> RateChange | None:
    if entry is None:
        return None
    return RateChange(rate_cents=entry.rate_cents, effective_date=entry.effective_date)


def rate_card(db: Session, provider: Provider, today: date) -> list[RateCardRow]:
    rows = []
    for payer, cpt_code in rates_repo.contracted_codes(db, provider.id):
        current = rates_repo.in_effect(db, provider.id, payer, cpt_code, today)
        upcoming = rates_repo.next_change(db, provider.id, payer, cpt_code, today)
        rows.append(RateCardRow(payer=payer, cpt_code=cpt_code, current=_change(current), upcoming=_change(upcoming)))
    return rows
