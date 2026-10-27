from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from earnings.db import get_db
from earnings.repositories import providers as providers_repo
from earnings.schemas import EarningsSummary, MonthDetail
from earnings.services.earnings import month_detail, year_summary
from earnings.services.months import parse_month

router = APIRouter(prefix="/providers/{provider_id}", tags=["earnings"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/earnings", response_model=EarningsSummary)
def earnings_for_year(
    db: DbSession, provider_id: int, year: Annotated[int, Query(ge=2000, le=2100)]
) -> EarningsSummary:
    """Year-to-date earnings: totals, by month and by payer."""
    provider = providers_repo.get_provider(db, provider_id)
    return year_summary(db, provider, year)


@router.get("/earnings/{month}", response_model=MonthDetail)
def earnings_for_month(db: DbSession, provider_id: int, month: str) -> MonthDetail:
    """Every paid session in one month ("2026-07"), with the rate it paid."""
    provider = providers_repo.get_provider(db, provider_id)
    return month_detail(db, provider, parse_month(month))
