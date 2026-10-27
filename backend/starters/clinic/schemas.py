"""Pydantic models = the API contract (think zod schemas + TS types in one).

from_attributes=True lets a model be built from an ORM object: PatientOut.model_validate(orm_patient)
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payer_name: str
    plan_name: str
    copay_cents: int
    effective_date: date
    termination_date: date | None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    date_of_birth: date
    email: str
    status: str | None
    member_id: str | None
    insurance_plan: PlanOut | None


class PatientPage(BaseModel):
    items: list[PatientOut]
    total: int
    page: int
    page_size: int


class PatientCreate(BaseModel):
    """Body for POST /patients.

    Product requirements:
      - first_name / last_name: surrounding whitespace is trimmed; blank names are rejected
      - date_of_birth: an ISO date ("1990-04-12"); must not be in the future
      - email: must look like an email (something@domain.tld); stored lowercased
      - insurance_plan_id: optional (self-pay patients have none)
      - member_id: optional, BUT required when insurance_plan_id is provided
    Invalid input must produce a 422 response, never a 500.
    """

    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    insurance_plan_id: int | None = None
    member_id: str


class CoverageUpdate(BaseModel):
    """Body for PATCH /patients/{id}/coverage. Send insurance_plan_id=null to remove coverage."""

    insurance_plan_id: int | None
    member_id: str | None = None


class EligibilityOut(BaseModel):
    patient_id: int
    status: str
    reason: str
    checked_on: date
    plan: PlanOut | None


class AppointmentOut(BaseModel):
    id: int
    provider_name: str
    starts_at: datetime
    duration_minutes: int
    status: str
    display_time: str


class AppointmentsOut(BaseModel):
    upcoming: list[AppointmentOut]
    past: list[AppointmentOut]
