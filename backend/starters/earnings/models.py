"""ORM models. Money is integer cents everywhere. Dates of service are plain calendar dates."""

from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from earnings.db import Base


class SessionStatus(StrEnum):
    SCHEDULED = "scheduled"  # booked, hasn't happened yet
    COMPLETED = "completed"  # happened and was documented: the provider earns their contracted rate
    NO_SHOW = "no_show"  # not paid out to the provider
    CANCELLED = "cancelled"  # nothing to pay


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    npi: Mapped[str] = mapped_column(String(10), unique=True)
    license: Mapped[str] = mapped_column(String(10))  # "LCSW", "PsyD", "LPC", ...
    state: Mapped[str] = mapped_column(String(2))  # where they're licensed, e.g. "TX"

    rates: Mapped[list["ContractedRate"]] = relationship(back_populates="provider")


class ContractedRate(Base):
    """One entry in a provider's fee schedule.

    From `effective_date` on, Acme Health pays the provider `rate_cents` per session for this
    (payer, CPT code). Entries are never edited or deleted once they're in effect: see the README's
    "Rates" section for how rate changes and corrections are recorded.
    """

    __tablename__ = "contracted_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    payer: Mapped[str] = mapped_column(String(40))  # "Aetna", "Cigna", "Optum"
    cpt_code: Mapped[str] = mapped_column(String(5))  # 90791 intake, 90834 45 min, 90837 60 min
    rate_cents: Mapped[int]
    effective_date: Mapped[date]
    created_at: Mapped[datetime]  # when ops entered it (naive UTC)
    note: Mapped[str] = mapped_column(String(200), default="")

    provider: Mapped[Provider] = relationship(back_populates="rates")


class Appointment(Base):
    """One therapy session (called an appointment so it isn't confused with a DB Session)."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    client_name: Mapped[str] = mapped_column(String(120))  # "Last, First"
    service_date: Mapped[date] = mapped_column(index=True)  # the provider's calendar date
    start_time: Mapped[time]  # provider-local wall clock time, for display
    cpt_code: Mapped[str] = mapped_column(String(5))
    payer: Mapped[str] = mapped_column(String(40))
    status: Mapped[SessionStatus] = mapped_column(String(20))
    paid_on: Mapped[date | None] = mapped_column(default=None)  # when Acme Health paid it out (None: not yet)


class Adjustment(Base):
    """A manual correction to a provider's pay: clawbacks (negative) or one-off payments.

    Paid out on its effective_date. Adjustments appear on pay statements, not on the earnings dashboard.
    """

    __tablename__ = "adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    effective_date: Mapped[date]
    amount_cents: Mapped[int]
    reason: Mapped[str] = mapped_column(String(200))
