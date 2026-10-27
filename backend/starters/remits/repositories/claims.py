from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from remits.errors import NotFound
from remits.models import Claim, ClaimPayment

_WITH_PAYMENTS = (
    selectinload(Claim.provider),
    selectinload(Claim.payments).selectinload(ClaimPayment.adjustments),
    selectinload(Claim.payments).selectinload(ClaimPayment.remittance),
)


def get_by_number(db: Session, claim_number: str) -> Claim:
    claim = db.scalar(select(Claim).where(Claim.claim_number == claim_number).options(*_WITH_PAYMENTS))
    if claim is None:
        raise NotFound(f"Claim {claim_number} not found", code="claim_not_found")
    return claim


def list_claims(db: Session, *, payer: str | None = None, search: str | None = None) -> list[Claim]:
    """Newest date of service first. `search` matches the claim number or the patient's name."""
    stmt = select(Claim).options(*_WITH_PAYMENTS)
    if payer:
        stmt = stmt.where(Claim.payer == payer)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(Claim.claim_number.ilike(pattern), Claim.patient_name.ilike(pattern)))
    stmt = stmt.order_by(Claim.date_of_service.desc(), Claim.claim_number)
    return list(db.scalars(stmt))
