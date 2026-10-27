from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from remits.errors import NotFound
from remits.models import ClaimPayment, Remittance, SuspenseLine

_WITH_LINES = (
    selectinload(Remittance.payments).selectinload(ClaimPayment.adjustments),
    selectinload(Remittance.payments).selectinload(ClaimPayment.claim),
    selectinload(Remittance.remit_adjustments),
    selectinload(Remittance.suspense_lines),
)


def get(db: Session, remittance_id: int) -> Remittance:
    remittance = db.scalar(select(Remittance).where(Remittance.id == remittance_id).options(*_WITH_LINES))
    if remittance is None:
        raise NotFound(f"Remittance {remittance_id} not found", code="remittance_not_found")
    return remittance


def find_by_trace(db: Session, payer: str, trace_number: str) -> Remittance | None:
    """The payment this payer already sent with this trace number, if we've seen it."""
    stmt = select(Remittance).where(Remittance.payer == payer, Remittance.trace_number == trace_number)
    return db.scalar(stmt)


def list_all(db: Session, *, payer: str | None = None) -> list[Remittance]:
    """Most recent payment first."""
    stmt = select(Remittance).options(*_WITH_LINES)
    if payer:
        stmt = stmt.where(Remittance.payer == payer)
    return list(db.scalars(stmt.order_by(Remittance.paid_on.desc(), Remittance.id.desc())))


def payment_for(db: Session, remittance_id: int, claim_id: int) -> ClaimPayment | None:
    """The line of this remittance that pays this claim, if it was already posted."""
    stmt = select(ClaimPayment).where(
        ClaimPayment.remittance_id == remittance_id, ClaimPayment.claim_id == claim_id
    )
    return db.scalar(stmt)


def open_suspense(db: Session) -> list[SuspenseLine]:
    """Unmatched lines still waiting for someone to match them, oldest first."""
    stmt = (
        select(SuspenseLine)
        .where(SuspenseLine.matched_claim_id.is_(None))
        .options(selectinload(SuspenseLine.remittance))
        .order_by(SuspenseLine.id)
    )
    return list(db.scalars(stmt))


def get_suspense(db: Session, suspense_id: int) -> SuspenseLine:
    line = db.get(SuspenseLine, suspense_id)
    if line is None:
        raise NotFound(f"Suspense line {suspense_id} not found", code="suspense_not_found")
    return line
