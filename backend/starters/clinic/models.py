from datetime import date, datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clinic.db import Base


class InsurancePlan(Base):
    __tablename__ = "insurance_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    payer_name: Mapped[str] = mapped_column(String(100))
    plan_name: Mapped[str] = mapped_column(String(100))
    copay_cents: Mapped[int] = mapped_column(default=0)
    effective_date: Mapped[date]
    # Last day of coverage (inclusive). None = open-ended.
    termination_date: Mapped[date | None]


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date]
    email: Mapped[str] = mapped_column(String(255))
    # "active" | "archived". Rows imported from the legacy system have NULL (treat as active).
    status: Mapped[str | None] = mapped_column(String(20))
    insurance_plan_id: Mapped[int | None] = mapped_column(ForeignKey("insurance_plans.id"))
    member_id: Mapped[str | None] = mapped_column(String(50))

    insurance_plan: Mapped[InsurancePlan | None] = relationship()
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    provider_name: Mapped[str] = mapped_column(String(100))
    starts_at: Mapped[datetime]
    duration_minutes: Mapped[int] = mapped_column(default=50)
    # "scheduled" | "completed" | "cancelled"
    status: Mapped[str] = mapped_column(String(20), default="scheduled")

    patient: Mapped[Patient] = relationship(back_populates="appointments")
