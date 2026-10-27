from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from clinic import repository
from clinic.db import get_db
from clinic.models import InsurancePlan, Patient
from clinic.schemas import (
    AppointmentsOut,
    CoverageUpdate,
    EligibilityOut,
    PatientCreate,
    PatientOut,
    PatientPage,
    PlanOut,
)
from clinic.services import patient_cache
from clinic.services.appointments import past_appointments, upcoming_appointments
from clinic.services.eligibility import check_eligibility

router = APIRouter(prefix="/patients", tags=["patients"])

DbSession = Annotated[Session, Depends(get_db)]


def _get_patient_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return patient


def _require_plan_exists(db: Session, plan_id: int | None) -> None:
    if plan_id is not None and db.get(InsurancePlan, plan_id) is None:
        raise HTTPException(status_code=422, detail=f"Unknown insurance plan {plan_id}")


@router.get("", response_model=PatientPage)
def list_patients(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    payer: str | None = None,
    include_archived: bool = False,
) -> PatientPage:
    items, total = repository.list_patients(
        db, payer=payer, include_archived=include_archived, page=page, page_size=page_size
    )
    return PatientPage(
        items=[PatientOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: DbSession) -> PatientOut:
    _require_plan_exists(db, payload.insurance_plan_id)
    patient = Patient(**payload.model_dump(), status="active")
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return PatientOut.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: DbSession) -> PatientOut:
    detail = patient_cache.get_patient_detail(db, patient_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return detail


@router.patch("/{patient_id}/coverage", response_model=PatientOut)
def update_coverage(patient_id: int, payload: CoverageUpdate, db: DbSession) -> PatientOut:
    patient = _get_patient_or_404(db, patient_id)
    _require_plan_exists(db, payload.insurance_plan_id)

    patient.insurance_plan_id = payload.insurance_plan_id
    patient.member_id = payload.member_id
    db.commit()

    detail = patient_cache.get_patient_detail(db, patient_id)
    assert detail is not None
    return detail


@router.get("/{patient_id}/eligibility", response_model=EligibilityOut)
def get_eligibility(patient_id: int, db: DbSession, on: date | None = None) -> EligibilityOut:
    patient = _get_patient_or_404(db, patient_id)
    checked_on = on or date.today()
    result = check_eligibility(patient.insurance_plan, patient.member_id, checked_on)
    return EligibilityOut(
        patient_id=patient.id,
        status=result.status,
        reason=result.reason,
        checked_on=checked_on,
        plan=PlanOut.model_validate(patient.insurance_plan) if patient.insurance_plan else None,
    )


@router.get("/{patient_id}/appointments", response_model=AppointmentsOut)
def get_appointments(
    patient_id: int, db: DbSession, now: datetime | None = None
) -> AppointmentsOut:
    patient = _get_patient_or_404(db, patient_id)
    current = now or datetime.now()
    return AppointmentsOut(
        upcoming=upcoming_appointments(patient.appointments, current),
        past=past_appointments(patient.appointments, current),
    )
