"""Pydantic response models (the API contract the portal relies on)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    npi: str
    timezone: str


class StatementLine(BaseModel):
    appointment_id: int
    service_date: date  # the date of service, as the provider would write it down
    starts_at: datetime  # aware UTC
    client_name: str
    cpt_code: str
    payer: str
    status: str
    kind: str  # "session" | "late_cancel"
    amount_cents: int


class AdjustmentLine(BaseModel):
    id: int | None  # None for a carryover (computed, not stored)
    effective_date: date
    reason: str
    amount_cents: int


class Statement(BaseModel):
    provider: ProviderOut
    period_start: date
    period_end: date  # inclusive
    lines: list[StatementLine]
    adjustments: list[AdjustmentLine]
    total_cents: int  # net: sessions + adjustments + any carryover in (can be negative)
    payout_cents: int  # what is actually sent: never negative
    pay_date: date | None = None


class PeriodSummary(BaseModel):
    period_start: date
    period_end: date
    session_count: int
    total_cents: int
    payout_cents: int
    pay_date: date | None = None
