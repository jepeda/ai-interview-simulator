"""Contract variance: claims the payer allowed for less than our contract says."""

from sqlalchemy.orm import Session

from remits.repositories import claims as claims_repo
from remits.repositories import fees as fees_repo
from remits.schemas import UnderpaymentOut, UnderpaymentReport
from remits.services.claims import totals

# Differences up to $1.00 aren't worth an appeal.
TOLERANCE_CENTS = 100


def underpayments(db: Session) -> UnderpaymentReport:
    contracts = fees_repo.fee_table(db)
    items: list[UnderpaymentOut] = []
    for claim in claims_repo.list_claims(db):
        t = totals(claim)
        if t.status not in ("paid", "partially_paid"):
            continue
        expected = contracts.get((claim.payer, claim.cpt_code))
        if expected is None:
            continue
        allowed = t.paid_cents + t.patient_resp_cents
        variance = expected - allowed
        if variance > TOLERANCE_CENTS:
            items.append(
                UnderpaymentOut(
                    claim_number=claim.claim_number,
                    patient_name=claim.patient_name,
                    payer=claim.payer,
                    cpt_code=claim.cpt_code,
                    date_of_service=claim.date_of_service,
                    expected_cents=expected,
                    allowed_cents=allowed,
                    variance_cents=variance,
                )
            )
    items.sort(key=lambda u: (-u.variance_cents, u.claim_number))
    return UnderpaymentReport(
        tolerance_cents=TOLERANCE_CENTS,
        total_variance_cents=sum(u.variance_cents for u in items),
        claims=items,
    )
