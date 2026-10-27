"""Pydantic response models (the API contract the dashboard relies on)."""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    npi: str
    license: str
    state: str


class RateEntryOut(BaseModel):
    """One fee-schedule entry, as ops entered it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    payer: str
    cpt_code: str
    rate_cents: int
    effective_date: date
    created_at: datetime
    note: str


class RateChange(BaseModel):
    rate_cents: int
    effective_date: date


class RateCardRow(BaseModel):
    """What the provider is paid today for one (payer, CPT), and the next scheduled change."""

    payer: str
    cpt_code: str
    current: RateChange | None  # None: the contract starts in the future
    upcoming: RateChange | None


class MonthEarnings(BaseModel):
    month: str  # "2026-07"
    session_count: int
    earned_cents: int


class PayerEarnings(BaseModel):
    payer: str
    session_count: int
    earned_cents: int


class EarningsSummary(BaseModel):
    provider: ProviderOut
    year: int
    session_count: int
    total_cents: int
    months: list[MonthEarnings]  # months with at least one paid session, oldest first
    by_payer: list[PayerEarnings]  # highest earnings first


class EarningLine(BaseModel):
    appointment_id: int
    service_date: date
    start_time: time
    client_name: str
    cpt_code: str
    payer: str
    rate_cents: int
    paid_on: date | None


class MonthDetail(BaseModel):
    provider_id: int
    month: str
    session_count: int
    total_cents: int
    lines: list[EarningLine]
