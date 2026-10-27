"""Claim balances and statuses, derived from everything posted to the claim.

    balance = billed - paid - adjusted (CO/OA/PI) - patient responsibility (PR)

A fully adjudicated claim balances to zero: every billed dollar was either paid by the payer,
written off under the contract, or moved to the client.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from remits import carc
from remits.models import Claim, ClaimPayment, PaymentAdjustment
from remits.repositories import claims as claims_repo
from remits.repositories import fees as fees_repo
from remits.schemas import AdjustmentOut, ClaimDetail, ClaimPaymentOut, ClaimStatus, ClaimSummary


@dataclass(frozen=True)
class ClaimTotals:
    paid_cents: int
    adjusted_cents: int
    patient_resp_cents: int
    balance_cents: int
    status: ClaimStatus


def totals(claim: Claim) -> ClaimTotals:
    paid = sum(p.paid_cents for p in claim.payments)
    adjustments = [a for p in claim.payments for a in p.adjustments]
    patient_resp = sum(a.amount_cents for a in adjustments if carc.is_patient_responsibility(a.group_code))
    adjusted = sum(a.amount_cents for a in adjustments if not carc.is_patient_responsibility(a.group_code))
    balance = claim.billed_cents - paid - adjusted - patient_resp
    return ClaimTotals(paid, adjusted, patient_resp, balance, _status(claim.payments, paid, balance))


def _status(payments: list[ClaimPayment], paid: int, balance: int) -> ClaimStatus:
    if not payments:
        return "submitted"
    if paid == 0 and any(carc.is_denial(a.group_code, a.reason_code) for p in payments for a in p.adjustments):
        return "denied"
    if balance > 0:
        return "partially_paid"
    if balance < 0:
        return "overpaid"
    return "paid"


def adjustment_out(adj: PaymentAdjustment) -> AdjustmentOut:
    return AdjustmentOut(
        group_code=adj.group_code,
        reason_code=adj.reason_code,
        code=carc.code_label(adj.group_code, adj.reason_code),
        description=carc.describe(adj.reason_code),
        amount_cents=adj.amount_cents,
    )


def summarize(claim: Claim) -> ClaimSummary:
    t = totals(claim)
    return ClaimSummary(
        claim_number=claim.claim_number,
        provider_name=claim.provider.name,
        patient_name=claim.patient_name,
        payer=claim.payer,
        cpt_code=claim.cpt_code,
        date_of_service=claim.date_of_service,
        billed_cents=claim.billed_cents,
        paid_cents=t.paid_cents,
        adjusted_cents=t.adjusted_cents,
        patient_resp_cents=t.patient_resp_cents,
        balance_cents=t.balance_cents,
        status=t.status,
    )


def claim_detail(db: Session, claim: Claim) -> ClaimDetail:
    payments = [
        ClaimPaymentOut(
            remittance_id=p.remittance_id,
            trace_number=p.remittance.trace_number,
            paid_on=p.remittance.paid_on,
            status_code=p.status_code,
            status_description=carc.CLAIM_STATUS_CODES.get(p.status_code, p.status_code),
            billed_cents=p.billed_cents,
            paid_cents=p.paid_cents,
            adjustments=[adjustment_out(a) for a in p.adjustments],
        )
        for p in claim.payments
    ]
    return ClaimDetail(
        **summarize(claim).model_dump(),
        contracted_allowed_cents=fees_repo.contracted_allowed(db, claim.payer, claim.cpt_code),
        payments=payments,
    )


def list_claims(
    db: Session, *, status: ClaimStatus | None = None, payer: str | None = None, search: str | None = None
) -> list[ClaimSummary]:
    summaries = [summarize(c) for c in claims_repo.list_claims(db, payer=payer, search=search)]
    return [s for s in summaries if status is None or s.status == status]
