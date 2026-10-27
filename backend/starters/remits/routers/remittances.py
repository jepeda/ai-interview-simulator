from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from remits.clock import get_now
from remits.db import get_db
from remits.repositories import remittances as remittances_repo
from remits.schemas import EraIn, RemittanceDetail, RemittanceSummary
from remits.services import remittances as remittances_service
from remits.services.posting import post_remittance

router = APIRouter(prefix="/remittances", tags=["remittances"])

DbSession = Annotated[Session, Depends(get_db)]
Now = Annotated[datetime, Depends(get_now)]


@router.get("", response_model=list[RemittanceSummary])
def list_remittances(db: DbSession, payer: str | None = None) -> list[RemittanceSummary]:
    """Remittances (ERAs), most recent payment first."""
    return [remittances_service.summarize(r) for r in remittances_repo.list_all(db, payer=payer)]


@router.get("/{remittance_id}", response_model=RemittanceDetail)
def get_remittance(db: DbSession, remittance_id: int) -> RemittanceDetail:
    return remittances_service.detail(remittances_repo.get(db, remittance_id))


@router.post("", response_model=RemittanceDetail, status_code=status.HTTP_201_CREATED)
def receive_remittance(db: DbSession, now: Now, era: EraIn) -> RemittanceDetail:
    """Called by the clearinghouse for every ERA (835) it receives from a payer."""
    return remittances_service.detail(post_remittance(db, era, received_at=now))
