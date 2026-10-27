from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from remits.db import get_db
from remits.repositories import claims as claims_repo
from remits.schemas import ClaimDetail, ClaimStatus, ClaimSummary
from remits.services import claims as claims_service

router = APIRouter(prefix="/claims", tags=["claims"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[ClaimSummary])
def list_claims(
    db: DbSession, status: ClaimStatus | None = None, payer: str | None = None, q: str | None = None
) -> list[ClaimSummary]:
    """Claims, newest date of service first. `q` searches claim number and patient name."""
    return claims_service.list_claims(db, status=status, payer=payer, search=q)


@router.get("/{claim_number}", response_model=ClaimDetail)
def get_claim(db: DbSession, claim_number: str) -> ClaimDetail:
    """One claim with every payment posted to it."""
    return claims_service.claim_detail(db, claims_repo.get_by_number(db, claim_number))
