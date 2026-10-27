from datetime import date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from booking.clock import Now
from booking.db import get_db
from booking.repositories import appointments as appointments_repo
from booking.repositories import providers as providers_repo
from booking.schemas import ProviderPage, ProviderSummary, SlotsOut
from booking.services.availability import open_slots
from booking.services.matching import SearchCriteria, search_providers
from booking.timeutil import to_db, zone

router = APIRouter(prefix="/providers", tags=["providers"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/search", response_model=ProviderPage)
def search(
    db: DbSession,
    now: Now,
    state: Annotated[str, Query(pattern=r"^[A-Za-z]{2}$", description="Two-letter state code")],
    payer: str | None = None,
    specialty: str | None = None,
    accepting_new_patients_only: bool = True,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> ProviderPage:
    criteria = SearchCriteria(
        state=state.upper(),
        payer=payer.strip() if payer and payer.strip() else None,
        specialty=specialty.strip().lower() if specialty and specialty.strip() else None,
        accepting_new_patients_only=accepting_new_patients_only,
        page=page,
        page_size=page_size,
    )
    providers, total = search_providers(db, criteria, today=now.date())
    return ProviderPage(
        items=[ProviderSummary.from_model(p) for p in providers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{provider_id}", response_model=ProviderSummary)
def get_provider(provider_id: int, db: DbSession) -> ProviderSummary:
    return ProviderSummary.from_model(providers_repo.get_provider(db, provider_id))


@router.get("/{provider_id}/slots", response_model=SlotsOut)
def get_slots(
    provider_id: int,
    db: DbSession,
    now: Now,
    date: date,  # noqa: A002 - query parameter name is part of the API
    tz: str | None = None,
) -> SlotsOut:
    provider = providers_repo.get_provider(db, provider_id)
    viewer_tz = zone(tz or provider.timezone)
    # Generous UTC range around the requested day: covers every timezone offset.
    day_start = datetime.combine(date, time.min, tzinfo=viewer_tz)
    appointments = appointments_repo.list_for_provider(
        db, provider.id, to_db(day_start - timedelta(days=2)), to_db(day_start + timedelta(days=3))
    )
    return SlotsOut(
        provider_id=provider.id,
        date=date,
        timezone=viewer_tz.key,
        slots=open_slots(provider, date, viewer_tz, appointments, now),
    )
