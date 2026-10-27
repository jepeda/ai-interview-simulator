"""Work queues for the revenue-cycle team: denials, underpayments, unmatched (suspense) lines."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from remits.clock import get_today
from remits.db import get_db
from remits.schemas import ClaimDetail, DenialQueue, MatchIn, SuspenseLineOut, UnderpaymentReport
from remits.services import claims as claims_service
from remits.services import suspense as suspense_service
from remits.services.denials import denial_queue
from remits.services.underpayments import underpayments

router = APIRouter(tags=["work queues"])

DbSession = Annotated[Session, Depends(get_db)]
Today = Annotated[date, Depends(get_today)]


@router.get("/denials", response_model=DenialQueue)
def denials(db: DbSession, today: Today, payer: str | None = None, code: str | None = None) -> DenialQueue:
    """Denied claims, oldest date of service first, bucketed by days outstanding."""
    return denial_queue(db, today, payer=payer, code=code)


@router.get("/underpayments", response_model=UnderpaymentReport)
def list_underpayments(db: DbSession) -> UnderpaymentReport:
    """Claims allowed for more than $1.00 below the contracted rate, biggest variance first."""
    return underpayments(db)


@router.get("/suspense", response_model=list[SuspenseLineOut])
def list_suspense(db: DbSession) -> list[SuspenseLineOut]:
    """Remittance lines we couldn't match to a claim, oldest first."""
    return suspense_service.open_lines(db)


@router.post("/suspense/{suspense_id}/match", response_model=ClaimDetail)
def match_suspense(db: DbSession, suspense_id: int, body: MatchIn) -> ClaimDetail:
    """Post a parked line to the right claim (as part of the remittance it came in)."""
    claim = suspense_service.match(db, suspense_id, body.claim_number)
    return claims_service.claim_detail(db, claim)
