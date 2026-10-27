from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from payouts.db import get_db
from payouts.repositories import providers as providers_repo
from payouts.schemas import PeriodSummary, Statement
from payouts.services.periods import period_starting
from payouts.services.statement_csv import statement_csv
from payouts.services.statements import build_statement, list_periods

router = APIRouter(prefix="/providers/{provider_id}", tags=["statements"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/periods", response_model=list[PeriodSummary])
def periods(db: DbSession, provider_id: int) -> list[PeriodSummary]:
    """Pay periods with activity, newest first."""
    provider = providers_repo.get_provider(db, provider_id)
    return list_periods(db, provider)


# Declared before /statements/{period_start}: that route would otherwise match "2026-10-01.csv"
# and reject it as an invalid date.
@router.get("/statements/{period_start}.csv", response_class=Response)
def statement_as_csv(db: DbSession, provider_id: int, period_start: date) -> Response:
    """The statement as CSV (one row per session/adjustment, then a Total row)."""
    provider = providers_repo.get_provider(db, provider_id)
    statement = build_statement(db, provider, period_starting(period_start))
    filename = f"statement-{period_start.isoformat()}.csv"
    return Response(
        content=statement_csv(statement),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/statements/{period_start}", response_model=Statement)
def statement(db: DbSession, provider_id: int, period_start: date) -> Statement:
    """The pay statement for the period starting on `period_start` (the 1st or the 16th)."""
    provider = providers_repo.get_provider(db, provider_id)
    return build_statement(db, provider, period_starting(period_start))
