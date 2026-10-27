"""Pydantic models = the API contract (think zod schemas + TS types in one).

from_attributes=True lets a model be built from an ORM object: PatientOut.model_validate(orm_patient)

Reference solution for PatientCreate. Fixes:
  - date_of_birth typed as `date` (Pydantic parses ISO strings; the ORM needs a real date)
  - member_id optional, with a cross-field rule in a model_validator
  - names trimmed + non-blank, email pattern + lowercased, future DOB rejected -> 422s
"""

from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


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

    first_name: Name
    last_name: Name
    date_of_birth: date
    email: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=EMAIL_PATTERN)]
    insurance_plan_id: int | None = None
    member_id: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value

    @model_validator(mode="after")
    def member_id_required_with_plan(self) -> Self:
        if self.insurance_plan_id is not None and not self.member_id:
            raise ValueError("member_id is required when insurance_plan_id is set")
        return self


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
