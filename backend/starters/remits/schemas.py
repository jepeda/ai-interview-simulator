"""Pydantic models: the ERA payload the clearinghouse POSTs, and the API the portal relies on."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from remits.money import AMOUNT_PATTERN

# Dollars as a decimal string, exactly as the 835 has it: "137.17", "-42.15", "25"
Amount = Annotated[str, StringConstraints(pattern=AMOUNT_PATTERN)]


# ── inbound: an ERA (835) translated to JSON by our clearinghouse ─────────────


class EraAdjustmentIn(BaseModel):
    group: Literal["CO", "PR", "OA", "PI"]
    reason: str = Field(min_length=1, max_length=5, examples=["45"])
    amount: Amount


class EraClaimIn(BaseModel):
    claim_number: str = Field(examples=["HW-1042"])
    status_code: Literal["1", "2", "4", "22"] = "1"
    billed: Amount
    paid: Amount
    adjustments: list[EraAdjustmentIn] = []


class EraRemitAdjustmentIn(BaseModel):
    code: str = Field(min_length=2, max_length=3, examples=["WO"])
    reference: str = ""
    amount: Amount  # signed from Acme Health's side: "-42.15" = the payer took money back


class EraIn(BaseModel):
    payer: str = Field(examples=["Optum"])
    trace_number: str = Field(min_length=1, max_length=50, examples=["1102948731"])
    payment_method: Literal["ACH", "CHK"] = "ACH"
    paid_on: date
    total_paid: Amount
    claims: list[EraClaimIn] = Field(min_length=1)
    remit_adjustments: list[EraRemitAdjustmentIn] = []


# ── outbound ──────────────────────────────────────────────────────────────────


class AdjustmentOut(BaseModel):
    group_code: str
    reason_code: str
    code: str  # "CO-45"
    description: str
    amount_cents: int


class ClaimPaymentOut(BaseModel):
    remittance_id: int
    trace_number: str
    paid_on: date
    status_code: str
    status_description: str
    billed_cents: int
    paid_cents: int
    adjustments: list[AdjustmentOut]


ClaimStatus = Literal["submitted", "paid", "partially_paid", "overpaid", "denied"]


class ClaimSummary(BaseModel):
    claim_number: str
    provider_name: str
    patient_name: str
    payer: str
    cpt_code: str
    date_of_service: date
    billed_cents: int
    paid_cents: int  # by the payer, all remits
    adjusted_cents: int  # CO/OA/PI adjustments: written off, never billed to the patient
    patient_resp_cents: int  # PR adjustments: billed to the client
    balance_cents: int  # billed - paid - adjusted - patient_resp
    status: ClaimStatus


class ClaimDetail(ClaimSummary):
    contracted_allowed_cents: int | None  # from the fee schedule (None: no contract on file)
    payments: list[ClaimPaymentOut]


class RemitLineOut(BaseModel):
    claim_number: str
    patient_name: str
    status_code: str
    billed_cents: int
    paid_cents: int
    adjustments: list[AdjustmentOut]


class RemitAdjustmentOut(BaseModel):
    code: str
    description: str
    reference: str
    amount_cents: int


class RemittanceSummary(BaseModel):
    id: int
    payer: str
    trace_number: str
    payment_method: str
    paid_on: date
    received_at: datetime  # aware UTC
    total_paid_cents: int  # what the payer says it sent (BPR02)
    posted_cents: int  # what we posted: claim payments + remit-level adjustments
    out_of_balance_cents: int  # total_paid - posted; must be 0 before month-end close
    claim_count: int


class RemittanceDetail(RemittanceSummary):
    lines: list[RemitLineOut]
    remit_adjustments: list[RemitAdjustmentOut]
