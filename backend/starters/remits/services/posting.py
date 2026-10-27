"""Cash posting: apply an ERA (835) from a payer to our claims.

The clearinghouse POSTs each ERA to /remittances as JSON (see schemas.EraIn). Posting creates one
Remittance, one ClaimPayment per claim line (with its CAS adjustments) and the remit-level (PLB)
adjustments. It's all-or-nothing: if any line can't be posted, nothing is.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from remits.errors import InvalidRequest
from remits.models import ClaimPayment, PaymentAdjustment, RemitAdjustment, Remittance
from remits.money import to_cents
from remits.repositories import claims as claims_repo
from remits.repositories import remittances as remittances_repo
from remits.schemas import EraClaimIn, EraIn
from remits.timeutil import to_db


def post_remittance(db: Session, era: EraIn, received_at: datetime) -> Remittance:
    try:
        remittance = Remittance(
            payer=era.payer,
            trace_number=era.trace_number.strip(),
            payment_method=era.payment_method,
            paid_on=era.paid_on,
            total_paid_cents=to_cents(era.total_paid),
            received_at=to_db(received_at),
        )
        db.add(remittance)
        db.flush()

        for line in era.claims:
            _post_claim_line(db, remittance, line)
        for adj in era.remit_adjustments:
            db.add(
                RemitAdjustment(
                    remittance_id=remittance.id,
                    code=adj.code,
                    reference=adj.reference,
                    amount_cents=to_cents(adj.amount),
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return remittances_repo.get(db, remittance.id)


def _post_claim_line(db: Session, remittance: Remittance, line: EraClaimIn) -> ClaimPayment:
    claim = claims_repo.get_by_number(db, line.claim_number)
    if claim.payer != remittance.payer:
        raise InvalidRequest(
            f"Claim {claim.claim_number} was billed to {claim.payer}, not {remittance.payer}",
            code="payer_mismatch",
        )
    if remittances_repo.payment_for(db, remittance.id, claim.id) is not None:
        raise InvalidRequest(
            f"Claim {claim.claim_number} appears twice in remittance {remittance.trace_number}",
            code="duplicate_claim_line",
        )

    payment = ClaimPayment(
        remittance_id=remittance.id,
        claim_id=claim.id,
        status_code=line.status_code,
        billed_cents=to_cents(line.billed),
        paid_cents=to_cents(line.paid),
    )
    db.add(payment)
    db.flush()
    for adj in line.adjustments:
        db.add(
            PaymentAdjustment(
                payment_id=payment.id,
                group_code=adj.group,
                reason_code=adj.reason,
                amount_cents=to_cents(adj.amount),
            )
        )
    return payment
