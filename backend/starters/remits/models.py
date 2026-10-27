"""ORM models. Money is integer cents everywhere; datetimes are naive UTC.

    Claim 1──* ClaimPayment *──1 Remittance 1──* RemitAdjustment
                    1
                    *
            PaymentAdjustment (CAS: CO-45, PR-3, ...)
"""

from datetime import date, datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from remits.db import Base


class Provider(Base):
    """The therapist who rendered the service (Acme Health bills on their behalf)."""

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    npi: Mapped[str] = mapped_column(String(10), unique=True)


class FeeSchedule(Base):
    """Acme Health's contracted ALLOWED amount with a payer for one CPT code."""

    __tablename__ = "fee_schedules"
    __table_args__ = (UniqueConstraint("payer", "cpt_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    payer: Mapped[str] = mapped_column(String(40))
    cpt_code: Mapped[str] = mapped_column(String(5))
    allowed_cents: Mapped[int]


class Claim(Base):
    """One session billed to one payer (the 837 we sent)."""

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_number: Mapped[str] = mapped_column(String(20), unique=True)  # "HW-1042" (CLP01 on the 835)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    patient_name: Mapped[str] = mapped_column(String(120))  # "Last, First"
    payer: Mapped[str] = mapped_column(String(40))
    cpt_code: Mapped[str] = mapped_column(String(5))
    date_of_service: Mapped[date]
    billed_cents: Mapped[int]  # our charge (chargemaster), not what we expect to be paid

    provider: Mapped[Provider] = relationship()
    payments: Mapped[list["ClaimPayment"]] = relationship(
        back_populates="claim", order_by="ClaimPayment.id"
    )


class Remittance(Base):
    """One payment from a payer (one 835 / ERA): an EFT or a paper check covering many claims."""

    __tablename__ = "remittances"

    id: Mapped[int] = mapped_column(primary_key=True)
    payer: Mapped[str] = mapped_column(String(40))
    trace_number: Mapped[str] = mapped_column(String(50), index=True)  # TRN02: EFT trace / check no.
    payment_method: Mapped[str] = mapped_column(String(3))  # "ACH" | "CHK"
    paid_on: Mapped[date]
    total_paid_cents: Mapped[int]  # BPR02: the amount that hits the bank
    received_at: Mapped[datetime]  # naive UTC: when the file reached us

    payments: Mapped[list["ClaimPayment"]] = relationship(
        back_populates="remittance", order_by="ClaimPayment.id"
    )
    remit_adjustments: Mapped[list["RemitAdjustment"]] = relationship(
        back_populates="remittance", order_by="RemitAdjustment.id"
    )


class ClaimPayment(Base):
    """One claim line of a remittance (CLP), posted to the claim."""

    __tablename__ = "claim_payments"
    __table_args__ = (UniqueConstraint("remittance_id", "claim_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    remittance_id: Mapped[int] = mapped_column(ForeignKey("remittances.id"), index=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), index=True)
    status_code: Mapped[str] = mapped_column(String(3))  # CLP02: 1 processed, 4 denied, 22 reversal
    billed_cents: Mapped[int]  # CLP03, as the payer echoed it
    paid_cents: Mapped[int]  # CLP04 (negative on a reversal)

    claim: Mapped[Claim] = relationship(back_populates="payments")
    remittance: Mapped[Remittance] = relationship(back_populates="payments")
    adjustments: Mapped[list["PaymentAdjustment"]] = relationship(
        back_populates="payment", order_by="PaymentAdjustment.id"
    )


class PaymentAdjustment(Base):
    """A CAS adjustment on a claim line: group code + reason code + amount (CO-45 $37.83)."""

    __tablename__ = "payment_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("claim_payments.id"), index=True)
    group_code: Mapped[str] = mapped_column(String(2))  # CO, PR, OA, PI
    reason_code: Mapped[str] = mapped_column(String(5))  # CARC: 45, 1, 2, 3, 197...
    amount_cents: Mapped[int]

    payment: Mapped[ClaimPayment] = relationship(back_populates="adjustments")


class RemitAdjustment(Base):
    """PLB: a remit-level adjustment, e.g. recouping an overpayment on an older claim (negative)."""

    __tablename__ = "remit_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    remittance_id: Mapped[int] = mapped_column(ForeignKey("remittances.id"), index=True)
    code: Mapped[str] = mapped_column(String(3))  # WO overpayment recovery, L6 interest, ...
    reference: Mapped[str] = mapped_column(String(50))  # usually the claim it relates to
    amount_cents: Mapped[int]  # signed from Acme Health's side: negative = taken back

    remittance: Mapped[Remittance] = relationship(back_populates="remit_adjustments")
