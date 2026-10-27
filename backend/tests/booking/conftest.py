"""Fixtures for the booking project. Time is frozen: NOW is Monday 2026-10-26 08:00 in New York."""

from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from booking.clock import get_now
from booking.db import Base, get_db
from booking.main import app
from booking.models import (
    Appointment,
    AvailabilityWindow,
    Patient,
    Provider,
    ProviderLicense,
    ProviderPayer,
    Specialty,
)
from booking.timeutil import to_db

NOW = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)  # Monday; New York is still on EDT (UTC-4)
FAR_FUTURE = date(2027, 12, 31)


class Clock:
    def __init__(self) -> None:
        self.now = NOW


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db: Session, clock: Clock) -> Iterator[TestClient]:
    def override_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_now] = lambda: clock.now
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_provider(db: Session) -> Callable[..., Provider]:
    def _make(
        first_name: str = "Maya",
        last_name: str = "Rivera",
        *,
        tz: str = "America/New_York",
        rate: int = 15000,
        rating: float | None = 4.5,
        accepting: bool = True,
        licenses: dict[str, date] | None = None,
        payers: list[str] | None = None,
        specialties: list[str] | None = None,
        windows: list[tuple[int, str, str]] | None = None,
    ) -> Provider:
        provider = Provider(
            first_name=first_name, last_name=last_name, credential="LCSW", timezone=tz,
            session_minutes=50, session_rate_cents=rate, rating=rating, accepting_new_patients=accepting,
        )
        provider.licenses = [
            ProviderLicense(state=s, expires_on=exp) for s, exp in (licenses or {"NY": FAR_FUTURE}).items()
        ]
        provider.payers = [ProviderPayer(payer_name=p) for p in (payers if payers is not None else ["Aetna"])]
        for slug in specialties if specialties is not None else ["anxiety"]:
            spec = db.scalar(select(Specialty).where(Specialty.slug == slug))
            provider.specialties.append(spec or Specialty(slug=slug, name=slug.title()))
        provider.availability = [
            AvailabilityWindow(weekday=wd, start_time=time.fromisoformat(s), end_time=time.fromisoformat(e))
            for wd, s, e in (windows if windows is not None else [(0, "09:00", "12:00")])
        ]
        db.add(provider)
        db.commit()
        return provider

    return _make


@pytest.fixture
def make_patient(db: Session) -> Callable[..., Patient]:
    def _make(state: str = "NY", payer: str | None = "Aetna") -> Patient:
        patient = Patient(first_name="Jordan", last_name="Lee", state=state, payer_name=payer)
        db.add(patient)
        db.commit()
        return patient

    return _make


@pytest.fixture
def make_appointment(db: Session) -> Callable[..., Appointment]:
    def _make(provider: Provider, patient: Patient, starts_at: datetime, status: str = "booked") -> Appointment:
        appointment = Appointment(
            provider_id=provider.id,
            patient_id=patient.id,
            starts_at=to_db(starts_at),
            ends_at=to_db(starts_at + timedelta(minutes=provider.session_minutes)),
            status=status,
            created_at=to_db(NOW),
        )
        db.add(appointment)
        db.commit()
        return appointment

    return _make
