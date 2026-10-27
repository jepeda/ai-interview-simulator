"""Suspense: remittance lines we couldn't match to a claim, and matching them by hand."""

from sqlalchemy.orm import Session

from remits.errors import Conflict
from remits.models import Claim
from remits.repositories import claims as claims_repo
from remits.repositories import remittances as remittances_repo
from remits.schemas import EraClaimIn, SuspenseLineOut
from remits.services.posting import post_claim_line
from remits.services.remittances import suspense_line_out


def open_lines(db: Session) -> list[SuspenseLineOut]:
    return [suspense_line_out(line) for line in remittances_repo.open_suspense(db)]


def match(db: Session, suspense_id: int, claim_number: str) -> Claim:
    """Post a parked line to `claim_number`, as part of the remittance it arrived in."""
    parked = remittances_repo.get_suspense(db, suspense_id)
    if parked.matched_claim_id is not None:
        raise Conflict(f"Suspense line {suspense_id} was already matched", code="already_matched")
    claim = claims_repo.get_by_number(db, claim_number.strip())

    line = EraClaimIn.model_validate_json(parked.line_json)
    try:
        post_claim_line(db, parked.remittance, claim, line)
        parked.matched_claim_id = claim.id
        db.commit()
    except Exception:
        db.rollback()
        raise
    return claims_repo.get_by_number(db, claim.claim_number)
