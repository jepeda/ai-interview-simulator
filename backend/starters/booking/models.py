from datetime import date, datetime, time

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from booking.db import Base

provider_specialties = Table(
    "provider_specialties",
    Base.metadata,
    Column("provider_id", ForeignKey("providers.id"), primary_key=True),
    Column("specialty_id", ForeignKey("specialties.id"), primary_key=True),
)


class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)  # e.g. "anxiety"
    name: Mapped[str] = mapped_column(String(100))


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    credential: Mapped[str] = mapped_column(String(20))  # LCSW, PhD, LMFT, ...
    timezone: Mapped[str] = mapped_column(String(64))  # IANA name, e.g. "America/New_York"
    session_minutes: Mapped[int] = mapped_column(default=50)
    session_rate_cents: Mapped[int]
    accepting_new_patients: Mapped[bool] = mapped_column(default=True)
    rating: Mapped[float | None]  # None = not enough reviews yet

    licenses: Mapped[list["ProviderLicense"]] = relationship(back_populates="provider")
    payers: Mapped[list["ProviderPayer"]] = relationship(back_populates="provider")
    specialties: Mapped[list[Specialty]] = relationship(secondary=provider_specialties)
    availability: Mapped[list["AvailabilityWindow"]] = relationship(back_populates="provider")


class ProviderLicense(Base):
    """A provider may only see patients located in a state where they hold an unexpired license."""

    __tablename__ = "provider_licenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    state: Mapped[str] = mapped_column(String(2))  # "NY"
    expires_on: Mapped[date]  # last valid day (inclusive)

    provider: Mapped[Provider] = relationship(back_populates="licenses")


class ProviderPayer(Base):
    """An insurance payer the provider is in-network with."""

    __tablename__ = "provider_payers"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    payer_name: Mapped[str] = mapped_column(String(100))  # "Aetna" (compare case-insensitively)

    provider: Mapped[Provider] = relationship(back_populates="payers")


class AvailabilityWindow(Base):
    """A weekly recurring window, in the PROVIDER's local timezone. weekday: 0 = Monday ... 6 = Sunday."""

    __tablename__ = "availability_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    weekday: Mapped[int]
    start_time: Mapped[time]
    end_time: Mapped[time]

    provider: Mapped[Provider] = relationship(back_populates="availability")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2))  # where the patient is located
    payer_name: Mapped[str | None] = mapped_column(String(100))  # None = self-pay


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    starts_at: Mapped[datetime]  # naive UTC
    ends_at: Mapped[datetime]  # naive UTC
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked | cancelled | completed
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime]  # naive UTC
    cancelled_at: Mapped[datetime | None]  # naive UTC
    cancelled_by: Mapped[str | None] = mapped_column(String(20))  # patient | provider
    cancel_reason: Mapped[str | None] = mapped_column(String(500))
    late_cancel_fee_cents: Mapped[int] = mapped_column(default=0)

    provider: Mapped[Provider] = relationship()
    patient: Mapped[Patient] = relationship()
