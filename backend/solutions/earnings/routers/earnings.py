from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from earnings.clock import Today
from earnings.db import get_db
from earnings.repositories import providers as providers_repo
from earnings.schemas import EarningsSummary, MonthDetail, Projection, TaxSummary
from earnings.services.earnings import month_detail, year_summary
from earnings.services.months import parse_month
from earnings.services.projection import project_month
from earnings.services.tax import tax_summary

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


@router.get("/tax-summary/{year}", response_model=TaxSummary)
def tax_summary_for_year(
    db: DbSession, provider_id: int, year: Annotated[int, Path(ge=2000, le=2100)]
) -> TaxSummary:
    """What Acme Health paid the provider during `year` (by pay date), for their 1099-NEC."""
    provider = providers_repo.get_provider(db, provider_id)
    return tax_summary(db, provider, year)


@router.get("/projection/{month}", response_model=Projection)
def projection_for_month(db: DbSession, provider_id: int, month: str, today: Today) -> Projection:
    """Earned so far this month plus what booked sessions will add."""
    provider = providers_repo.get_provider(db, provider_id)
    return project_month(db, provider, parse_month(month), today)
