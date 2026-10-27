"""Remittance views: what a payer sent, what we posted from it, and whether the two agree."""

from remits import carc
from remits.models import Remittance, SuspenseLine
from remits.schemas import (
    RemitAdjustmentOut,
    RemitLineOut,
    RemittanceDetail,
    RemittanceSummary,
    SuspenseLineOut,
)
from remits.services.claims import adjustment_out
from remits.timeutil import from_db


def _open(remittance: Remittance) -> list[SuspenseLine]:
    return [s for s in remittance.suspense_lines if s.matched_claim_id is None]


def summarize(remittance: Remittance) -> RemittanceSummary:
    posted = sum(p.paid_cents for p in remittance.payments) + sum(
        a.amount_cents for a in remittance.remit_adjustments
    )
    suspense = sum(s.paid_cents for s in _open(remittance))
    return RemittanceSummary(
        id=remittance.id,
        payer=remittance.payer,
        trace_number=remittance.trace_number,
        payment_method=remittance.payment_method,
        paid_on=remittance.paid_on,
        received_at=from_db(remittance.received_at),
        total_paid_cents=remittance.total_paid_cents,
        posted_cents=posted,
        suspense_cents=suspense,
        out_of_balance_cents=remittance.total_paid_cents - posted - suspense,
        claim_count=len(remittance.payments),
    )


def suspense_line_out(line: SuspenseLine) -> SuspenseLineOut:
    return SuspenseLineOut(
        id=line.id,
        remittance_id=line.remittance_id,
        payer=line.remittance.payer,
        trace_number=line.remittance.trace_number,
        paid_on=line.remittance.paid_on,
        claim_number=line.claim_number,
        billed_cents=line.billed_cents,
        paid_cents=line.paid_cents,
    )


def detail(remittance: Remittance) -> RemittanceDetail:
    lines = [
        RemitLineOut(
            claim_number=p.claim.claim_number,
            patient_name=p.claim.patient_name,
            status_code=p.status_code,
            billed_cents=p.billed_cents,
            paid_cents=p.paid_cents,
            adjustments=[adjustment_out(a) for a in p.adjustments],
        )
        for p in remittance.payments
    ]
    remit_adjustments = [
        RemitAdjustmentOut(
            code=a.code,
            description=carc.REMIT_ADJUSTMENT_CODES.get(a.code, a.code),
            reference=a.reference,
            amount_cents=a.amount_cents,
        )
        for a in remittance.remit_adjustments
    ]
    return RemittanceDetail(
        **summarize(remittance).model_dump(),
        lines=lines,
        remit_adjustments=remit_adjustments,
        unmatched_lines=[suspense_line_out(s) for s in _open(remittance)],
    )
