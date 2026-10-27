"""Fixtures for the remits interview app: an in-memory DB, a client and small data factories."""

from collections.abc import Callable, Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from remits_testkit import BILLED
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from remits.clock import get_today
from remits.db import Base, get_db
from remits.main import app
from remits.models import Claim, FeeSchedule, Provider


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
def set_today(client: TestClient) -> Callable[[date], None]:
    """Pin the business date the app sees (clock.get_today)."""

    def pin(day: date) -> None:
        app.dependency_overrides[get_today] = lambda: day

    return pin


@pytest.fixture
def provider(db: Session) -> Provider:
    p = Provider(name="Dr. Test Provider", npi="1000000001")
    db.add(p)
    db.commit()
    return p


@pytest.fixture
def make_claim(db: Session, provider: Provider) -> Callable[..., Claim]:
    def make(
        claim_number: str,
        *,
        payer: str = "Aetna",
        cpt_code: str = "90837",
        date_of_service: date = date(2026, 9, 21),
        patient_name: str = "Doe, Jane",
    ) -> Claim:
        claim = Claim(
            claim_number=claim_number,
            provider_id=provider.id,
            patient_name=patient_name,
            payer=payer,
            cpt_code=cpt_code,
            date_of_service=date_of_service,
            billed_cents=BILLED[cpt_code],
        )
        db.add(claim)
        db.commit()
        return claim

    return make


@pytest.fixture
def make_fee(db: Session) -> Callable[[str, str, int], FeeSchedule]:
    def make(payer: str, cpt_code: str, allowed_cents: int) -> FeeSchedule:
        fee = FeeSchedule(payer=payer, cpt_code=cpt_code, allowed_cents=allowed_cents)
        db.add(fee)
        db.commit()
        return fee

    return make
