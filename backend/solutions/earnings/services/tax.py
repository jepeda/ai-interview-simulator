"""Annual 1099-NEC summary: what Acme Health PAID the provider during a calendar year (cash basis)."""

from datetime import date

from sqlalchemy.orm import Session

from earnings.models import Provider, SessionStatus
from earnings.repositories import adjustments as adjustments_repo
from earnings.repositories import appointments as appointments_repo
from earnings.schemas import PayerTotal, TaxSummary
from earnings.services.rates import load_rate_table

FORM_1099_THRESHOLD_CENTS = 60000  # $600


def tax_summary(db: Session, provider: Provider, year: int) -> TaxSummary:
    first, last = date(year, 1, 1), date(year, 12, 31)
    rates = load_rate_table(db, provider.id)

    payers: dict[str, PayerTotal] = {}
    for appt in appointments_repo.list_paid_between(db, provider.id, first, last):
        if appt.status != SessionStatus.COMPLETED:
            continue
        total = payers.setdefault(appt.payer, PayerTotal(payer=appt.payer, session_count=0, amount_cents=0))
        total.session_count += 1
        total.amount_cents += rates.rate_for(appt)  # the rate on the date of SERVICE

    sessions = sum(p.amount_cents for p in payers.values())
    adjustments = sum(a.amount_cents for a in adjustments_repo.list_between(db, provider.id, first, last))
    total = sessions + adjustments
    return TaxSummary(
        provider_id=provider.id,
        year=year,
        sessions_cents=sessions,
        adjustments_cents=adjustments,
        total_cents=total,
        by_payer=sorted(payers.values(), key=lambda p: (-p.amount_cents, p.payer)),
        form_1099_required=total >= FORM_1099_THRESHOLD_CENTS,
    )
