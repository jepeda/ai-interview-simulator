"""Cash posting: apply an ERA (835) from a payer to our claims.

The clearinghouse POSTs each ERA to /remittances as JSON (see schemas.EraIn). Posting creates one
Remittance, one ClaimPayment per claim line (with its CAS adjustments) and the remit-level (PLB)
adjustments. It's all-or-nothing: if any line can't be posted, nothing is.

Delivery is at-least-once: clearinghouses re-send files after outages and retries. A payment is
identified by payer + trace number (TRN02), so posting the same payment again is a no-op that
returns the remittance we already have (also enforced by a unique constraint, for races).

Lines for claim numbers we don't recognise don't block the rest of the payment: they're parked in
suspense (SuspenseLine) until someone matches them to the right claim (services/suspense.py).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from remits.errors import InvalidRequest
from remits.models import (
    Claim,
    ClaimPayment,
    PaymentAdjustment,
    RemitAdjustment,
    Remittance,
    SuspenseLine,
)
from remits.money import to_cents
from remits.repositories import claims as claims_repo
from remits.repositories import remittances as remittances_repo
from remits.schemas import EraClaimIn, EraIn
from remits.timeutil import to_db


@dataclass(frozen=True)
class PostingResult:
    remittance: Remittance
    created: bool  # False: we had already posted this payment (a re-delivered file)


def post_remittance(db: Session, era: EraIn, received_at: datetime) -> PostingResult:
    trace_number = era.trace_number.strip()
    existing = remittances_repo.find_by_trace(db, era.payer, trace_number)
    if existing is not None:
        return PostingResult(remittances_repo.get(db, existing.id), created=False)

    try:
        remittance = Remittance(
            payer=era.payer,
            trace_number=trace_number,
            payment_method=era.payment_method,
            paid_on=era.paid_on,
            total_paid_cents=to_cents(era.total_paid),
            received_at=to_db(received_at),
        )
        db.add(remittance)
        db.flush()

        for line in era.claims:
            claim = claims_repo.find_by_number(db, line.claim_number)
            if claim is None:
                _park_in_suspense(db, remittance, line)
            else:
                post_claim_line(db, remittance, claim, line)
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
    except IntegrityError:
        db.rollback()
        existing = remittances_repo.find_by_trace(db, era.payer, trace_number)
        if existing is None:
            raise
        return PostingResult(remittances_repo.get(db, existing.id), created=False)  # lost a race
    except Exception:
        db.rollback()
        raise
    return PostingResult(remittances_repo.get(db, remittance.id), created=True)


def post_claim_line(db: Session, remittance: Remittance, claim: Claim, line: EraClaimIn) -> ClaimPayment:
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


def _park_in_suspense(db: Session, remittance: Remittance, line: EraClaimIn) -> SuspenseLine:
    parked = SuspenseLine(
        remittance_id=remittance.id,
        claim_number=line.claim_number,
        billed_cents=to_cents(line.billed),
        paid_cents=to_cents(line.paid),
        line_json=line.model_dump_json(),
    )
    db.add(parked)
    return parked
