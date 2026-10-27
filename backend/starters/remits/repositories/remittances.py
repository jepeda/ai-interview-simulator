from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from remits.errors import NotFound
from remits.models import ClaimPayment, Remittance

_WITH_LINES = (
    selectinload(Remittance.payments).selectinload(ClaimPayment.adjustments),
    selectinload(Remittance.payments).selectinload(ClaimPayment.claim),
    selectinload(Remittance.remit_adjustments),
)


def get(db: Session, remittance_id: int) -> Remittance:
    remittance = db.scalar(select(Remittance).where(Remittance.id == remittance_id).options(*_WITH_LINES))
    if remittance is None:
        raise NotFound(f"Remittance {remittance_id} not found", code="remittance_not_found")
    return remittance


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
