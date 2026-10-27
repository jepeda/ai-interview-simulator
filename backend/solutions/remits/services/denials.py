"""Denial work queue: denied claims, oldest first, with AR aging buckets."""

from datetime import date

from sqlalchemy.orm import Session

from remits import carc
from remits.models import Claim, PaymentAdjustment
from remits.repositories import claims as claims_repo
from remits.schemas import AgingBucket, DenialOut, DenialQueue
from remits.services.claims import totals

# (label, last day in the bucket); anything older is "90+"
BUCKETS: list[tuple[AgingBucket, int]] = [("0-30", 30), ("31-60", 60), ("61-90", 90)]
OLDEST: AgingBucket = "90+"


def bucket_for(days_outstanding: int) -> AgingBucket:
    for label, last_day in BUCKETS:
        if days_outstanding <= last_day:
            return label
    return OLDEST


def _denial(claim: Claim) -> tuple[PaymentAdjustment, date]:
    """The denial adjustment from the most recent remittance that denied the claim."""
    for payment in reversed(claim.payments):
        for adj in payment.adjustments:
            if carc.is_denial(adj.group_code, adj.reason_code):
                return adj, payment.remittance.paid_on
    raise ValueError(f"{claim.claim_number} has no denial adjustment")


def denial_queue(db: Session, today: date, *, payer: str | None = None, code: str | None = None) -> DenialQueue:
    wanted_payer = payer.strip().lower() if payer else None
    wanted_code = code.strip().upper() if code else None

    items: list[DenialOut] = []
    for claim in claims_repo.list_claims(db):
        if totals(claim).status != "denied":
            continue
        if wanted_payer and claim.payer.lower() != wanted_payer:
            continue
        adj, denied_on = _denial(claim)
        label = carc.code_label(adj.group_code, adj.reason_code)
        if wanted_code and label != wanted_code:
            continue
        days = (today - claim.date_of_service).days
        items.append(
            DenialOut(
                claim_number=claim.claim_number,
                patient_name=claim.patient_name,
                provider_name=claim.provider.name,
                payer=claim.payer,
                cpt_code=claim.cpt_code,
                date_of_service=claim.date_of_service,
                billed_cents=claim.billed_cents,
                denial_code=label,
                denial_reason=carc.describe(adj.reason_code),
                denied_on=denied_on,
                days_outstanding=days,
                bucket=bucket_for(days),
            )
        )
    items.sort(key=lambda d: (-d.days_outstanding, d.claim_number))

    buckets: dict[AgingBucket, int] = {label: 0 for label, _ in BUCKETS} | {OLDEST: 0}
    for item in items:
        buckets[item.bucket] += 1
    return DenialQueue(as_of=today, buckets=buckets, claims=items)
