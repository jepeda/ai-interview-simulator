from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from payouts.db import get_db
from payouts.repositories import providers as providers_repo
from payouts.schemas import PeriodSummary, Statement
from payouts.services.periods import period_starting
from payouts.services.statements import build_statement, list_periods

router = APIRouter(prefix="/providers/{provider_id}", tags=["statements"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/periods", response_model=list[PeriodSummary])
def periods(db: DbSession, provider_id: int) -> list[PeriodSummary]:
    """Pay periods with activity, newest first."""
    provider = providers_repo.get_provider(db, provider_id)
    return list_periods(db, provider)


@router.get("/statements/{period_start}", response_model=Statement)
def statement(db: DbSession, provider_id: int, period_start: date) -> Statement:
    """The pay statement for the period starting on `period_start` (the 1st or the 16th)."""
    provider = providers_repo.get_provider(db, provider_id)
    return build_statement(db, provider, period_starting(period_start))
