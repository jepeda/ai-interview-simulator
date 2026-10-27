from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from earnings.clock import Today
from earnings.db import get_db
from earnings.repositories import providers as providers_repo
from earnings.repositories import rates as rates_repo
from earnings.schemas import RateCardRow, RateEntryOut
from earnings.services.rate_card import rate_card

router = APIRouter(prefix="/providers/{provider_id}", tags=["rates"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/rates", response_model=list[RateEntryOut])
def rate_history(db: DbSession, provider_id: int) -> list[RateEntryOut]:
    """Every fee-schedule entry, in the order ops entered them (internal: used by Network Ops)."""
    providers_repo.get_provider(db, provider_id)
    return [RateEntryOut.model_validate(e) for e in rates_repo.list_for_provider(db, provider_id)]


@router.get("/rate-card", response_model=list[RateCardRow])
def current_rate_card(db: DbSession, provider_id: int, today: Today) -> list[RateCardRow]:
    """What the provider is paid today per payer and service, plus scheduled changes."""
    provider = providers_repo.get_provider(db, provider_id)
    return rate_card(db, provider, today)
