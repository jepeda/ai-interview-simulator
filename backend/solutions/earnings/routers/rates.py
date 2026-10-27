from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from earnings.clock import Today
from earnings.db import get_db
from earnings.repositories import providers as providers_repo
from earnings.repositories import rates as rates_repo
from earnings.schemas import RateCardRow, RateChangeIn, RateEntryOut
from earnings.services.rate_card import rate_card
from earnings.services.rate_changes import cancel_rate_change, schedule_rate_change

router = APIRouter(prefix="/providers/{provider_id}", tags=["rates"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/rates", response_model=list[RateEntryOut])
def rate_history(db: DbSession, provider_id: int) -> list[RateEntryOut]:
    """Every fee-schedule entry, in the order ops entered them (internal: used by Network Ops)."""
    providers_repo.get_provider(db, provider_id)
    return [RateEntryOut.model_validate(e) for e in rates_repo.list_for_provider(db, provider_id)]


@router.post("/rates", response_model=RateEntryOut, status_code=201)
def schedule_rate(db: DbSession, provider_id: int, change: RateChangeIn, today: Today) -> RateEntryOut:
    """Schedule a future rate change for one payer and service (internal: Network Ops)."""
    provider = providers_repo.get_provider(db, provider_id)
    entered_at = datetime.now(UTC).replace(tzinfo=None)
    return RateEntryOut.model_validate(schedule_rate_change(db, provider, change, today, entered_at))


@router.delete("/rates/{rate_id}", status_code=204)
def cancel_rate(db: DbSession, provider_id: int, rate_id: int, today: Today) -> Response:
    """Cancel a scheduled rate change that hasn't taken effect yet."""
    provider = providers_repo.get_provider(db, provider_id)
    cancel_rate_change(db, provider, rate_id, today)
    return Response(status_code=204)


@router.get("/rate-card", response_model=list[RateCardRow])
def current_rate_card(db: DbSession, provider_id: int, today: Today) -> list[RateCardRow]:
    """What the provider is paid today per payer and service, plus scheduled changes."""
    provider = providers_repo.get_provider(db, provider_id)
    return rate_card(db, provider, today)
