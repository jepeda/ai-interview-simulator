"""Shared fixtures for the clinic debugging exercises.

Each test gets a brand-new in-memory SQLite database. StaticPool keeps the single
connection alive so the schema survives between sessions.
"""

from collections.abc import Callable, Iterator
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from clinic.db import Base, get_db
from clinic.main import app
from clinic.models import Appointment, InsurancePlan, Patient
from clinic.services import patient_cache


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    patient_cache.clear()
    try:
        yield TestClient(app)  # no `with`: skips the lifespan, so the demo seed never runs
    finally:
        app.dependency_overrides.clear()
        patient_cache.clear()


@pytest.fixture
def make_plan(db: Session) -> Callable[..., InsurancePlan]:
    def _make(**overrides) -> InsurancePlan:
        fields = {
            "payer_name": "Aetna",
            "plan_name": "Choice POS II",
            "copay_cents": 2500,
            "effective_date": date(2024, 1, 1),
            "termination_date": None,
        } | overrides
        plan = InsurancePlan(**fields)
        db.add(plan)
        db.commit()
        return plan

    return _make


@pytest.fixture
def make_patient(db: Session) -> Callable[..., Patient]:
    def _make(**overrides) -> Patient:
        fields = {
            "first_name": "Ada",
            "last_name": "King",
            "date_of_birth": date(1990, 12, 10),
            "email": "ada@example.com",
            "status": "active",
            "insurance_plan": None,
            "member_id": None,
        } | overrides
        patient = Patient(**fields)
        db.add(patient)
        db.commit()
        return patient

    return _make


@pytest.fixture
def make_appointment(db: Session) -> Callable[..., Appointment]:
    def _make(patient: Patient, starts_at: datetime, **overrides) -> Appointment:
        fields = {"provider_name": "Dr. Maya Lee", "status": "scheduled"} | overrides
        appt = Appointment(patient=patient, starts_at=starts_at, **fields)
        db.add(appt)
        db.commit()
        return appt

    return _make
