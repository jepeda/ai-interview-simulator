"""ORM models. Money is integer cents everywhere; datetimes are naive UTC (see timeutil.py)."""

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payouts.db import Base


class SessionStatus(StrEnum):
    COMPLETED = "completed"
    LATE_CANCEL = "late_cancel"  # cancelled < 24h before: the provider gets the late-cancel fee
    NO_SHOW = "no_show"  # not paid out (the patient no-show fee goes to Acme Health collections)
    CANCELLED = "cancelled"  # cancelled in time: nothing to pay


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    npi: Mapped[str] = mapped_column(String(10), unique=True)
    timezone: Mapped[str] = mapped_column(String(64))  # IANA name, e.g. "America/Los_Angeles"
    late_cancel_fee_cents: Mapped[int] = mapped_column(default=0)

    fees: Mapped[list["FeeSchedule"]] = relationship(back_populates="provider")


class FeeSchedule(Base):
    """The contracted rate Acme Health pays a provider for one CPT code with one payer."""

    __tablename__ = "fee_schedules"
    __table_args__ = (UniqueConstraint("provider_id", "payer", "cpt_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    payer: Mapped[str] = mapped_column(String(40))  # "Aetna", "Cigna", "Optum", "Self-pay"
    cpt_code: Mapped[str] = mapped_column(String(5))  # 90791 intake, 90834 45 min, 90837 60 min
    rate_cents: Mapped[int]

    provider: Mapped[Provider] = relationship(back_populates="fees")


class Appointment(Base):
    """One therapy session (called an appointment so it isn't confused with a DB Session)."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    client_name: Mapped[str] = mapped_column(String(120))  # "Last, First"
    starts_at: Mapped[datetime] = mapped_column(index=True)  # naive UTC
    cpt_code: Mapped[str] = mapped_column(String(5))
    payer: Mapped[str] = mapped_column(String(40))
    status: Mapped[SessionStatus] = mapped_column(String(20))

    provider: Mapped[Provider] = relationship()


class Adjustment(Base):
    """A manual correction to a provider's pay: clawbacks (negative) or catch-up payments.

    effective_date is a date in the provider's timezone; the adjustment lands on the statement of
    the pay period that contains that date.
    """

    __tablename__ = "adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    effective_date: Mapped[date]
    amount_cents: Mapped[int]
    reason: Mapped[str] = mapped_column(String(200))
