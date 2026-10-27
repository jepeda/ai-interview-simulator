"""Fixtures for the earnings interview app: an in-memory DB, a frozen "today", and data factories.

make_rate() records fee-schedule entries in the order the test calls it (each one is "entered" a
minute after the previous one), unless the test passes `entered=` explicitly.
"""

from collections.abc import Callable, Iterator
from datetime import date, datetime, time, timedelta

import pytest
from earnings_testkit import TODAY
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from earnings.clock import get_today
from earnings.db import Base, get_db
from earnings.main import app
from earnings.models import Adjustment, Appointment, ContractedRate, Provider, SessionStatus


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
def client(db: Session) -> Iterator[TestClient]:
    def override_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_today] = lambda: TODAY
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def set_today() -> Callable[[date], None]:
    def set_(day: date) -> None:
        app.dependency_overrides[get_today] = lambda: day

    return set_


@pytest.fixture
def make_provider(db: Session) -> Callable[..., Provider]:
    counter = iter(range(1, 1000))

    def make(name: str | None = None) -> Provider:
        n = next(counter)
        provider = Provider(name=name or f"Provider {n}", npi=f"{1000000000 + n}", license="LCSW", state="TX")
        db.add(provider)
        db.commit()
        return provider

    return make


@pytest.fixture
def make_rate(db: Session) -> Callable[..., ContractedRate]:
    clock = iter(datetime(2025, 12, 1, 9, 0) + timedelta(minutes=i) for i in range(100_000))

    def make(
        provider: Provider,
        payer: str,
        cpt_code: str,
        cents: int,
        effective: str,
        *,
        entered: str | None = None,
        note: str = "",
    ) -> ContractedRate:
        """`effective` is "YYYY-MM-DD"; `entered` (optional) is "YYYY-MM-DD HH:MM" UTC."""
        entry = ContractedRate(
            provider_id=provider.id,
            payer=payer,
            cpt_code=cpt_code,
            rate_cents=cents,
            effective_date=date.fromisoformat(effective),
            created_at=datetime.fromisoformat(entered) if entered else next(clock),
            note=note,
        )
        db.add(entry)
        db.commit()
        return entry

    return make


@pytest.fixture
def make_appointment(db: Session) -> Callable[..., Appointment]:
    def make(
        provider: Provider,
        day: str,
        *,
        client_name: str = "Doe, Jane",
        cpt_code: str = "90837",
        payer: str = "Aetna",
        status: SessionStatus = SessionStatus.COMPLETED,
        paid_on: str | None = None,
        start: str = "10:00",
    ) -> Appointment:
        appt = Appointment(
            provider_id=provider.id,
            client_name=client_name,
            service_date=date.fromisoformat(day),
            start_time=time.fromisoformat(start),
            cpt_code=cpt_code,
            payer=payer,
            status=status,
            paid_on=date.fromisoformat(paid_on) if paid_on else None,
        )
        db.add(appt)
        db.commit()
        return appt

    return make


@pytest.fixture
def make_adjustment(db: Session) -> Callable[..., Adjustment]:
    def make(provider: Provider, day: str, cents: int, reason: str = "Correction") -> Adjustment:
        adj = Adjustment(
            provider_id=provider.id, effective_date=date.fromisoformat(day), amount_cents=cents, reason=reason
        )
        db.add(adj)
        db.commit()
        return adj

    return make
