"""Fixtures for the payouts interview app: an in-memory DB and small data factories.

Appointment times are given in the provider's LOCAL time (like their calendar shows them) and
stored as naive UTC, exactly like seed.py does.
"""

from collections.abc import Callable, Iterator
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from payouts_testkit import LATE_CANCEL_FEE, RATE_90834, RATE_90837
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from payouts.db import Base, get_db
from payouts.main import app
from payouts.models import Adjustment, Appointment, FeeSchedule, Provider, SessionStatus
from payouts.timeutil import to_db, zone


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
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_provider(db: Session) -> Callable[..., Provider]:
    counter = iter(range(1, 1000))

    def make(timezone: str = "America/Los_Angeles", name: str | None = None) -> Provider:
        n = next(counter)
        provider = Provider(
            name=name or f"Provider {n}",
            npi=f"{1000000000 + n}",
            timezone=timezone,
            late_cancel_fee_cents=LATE_CANCEL_FEE,
        )
        db.add(provider)
        db.flush()
        for cpt, cents in (("90837", RATE_90837), ("90834", RATE_90834)):
            db.add(FeeSchedule(provider_id=provider.id, payer="Aetna", cpt_code=cpt, rate_cents=cents))
        db.commit()
        return provider

    return make


@pytest.fixture
def make_appointment(db: Session) -> Callable[..., Appointment]:
    def make(
        provider: Provider,
        local: str,
        *,
        client_name: str = "Doe, Jane",
        cpt_code: str = "90837",
        payer: str = "Aetna",
        status: SessionStatus = SessionStatus.COMPLETED,
    ) -> Appointment:
        """`local` is "YYYY-MM-DD HH:MM" on the provider's own clock."""
        starts = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=zone(provider.timezone))
        appt = Appointment(
            provider_id=provider.id,
            client_name=client_name,
            starts_at=to_db(starts),
            cpt_code=cpt_code,
            payer=payer,
            status=status,
        )
        db.add(appt)
        db.commit()
        return appt

    return make


@pytest.fixture
def make_adjustment(db: Session) -> Callable[..., Adjustment]:
    def make(provider: Provider, day: date, cents: int, reason: str = "Correction") -> Adjustment:
        adj = Adjustment(provider_id=provider.id, effective_date=day, amount_cents=cents, reason=reason)
        db.add(adj)
        db.commit()
        return adj

    return make
