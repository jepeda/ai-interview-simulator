"""Remittance codes: what the payer is telling us about each dollar.

An 835 explains every difference between what we billed and what the payer paid with a
CAS adjustment: a GROUP code (who owes it) plus a CARC reason code (why), e.g. CO-45.
"""

GROUP_CODES = {
    "CO": "Contractual obligation",  # we wrote it off: never billed to the patient
    "PR": "Patient responsibility",  # the client owes it (deductible, coinsurance, copay)
    "OA": "Other adjustment",
    "PI": "Payer initiated reduction",
}

# Claim Adjustment Reason Codes (CARC) we see from our payers.
REASON_CODES = {
    "1": "Deductible amount",
    "2": "Coinsurance amount",
    "3": "Co-payment amount",
    "16": "Claim lacks information needed for adjudication",
    "23": "Impact of prior payer adjudication",
    "29": "Time limit for filing has expired",
    "45": "Charge exceeds fee schedule / contracted amount",
    "50": "Not deemed a medical necessity",
    "96": "Non-covered charge",
    "197": "Precertification/authorization absent",
}

# Reasons that mean "we're not paying this claim" (as opposed to "we paid what the contract says").
DENIAL_REASONS = {"16", "29", "50", "96", "197"}

# CLP02 claim status codes.
CLAIM_STATUS_CODES = {
    "1": "Processed as primary",
    "2": "Processed as secondary",
    "4": "Denied",
    "22": "Reversal of previous payment",
}

# PLB: remit-level adjustments that aren't tied to one claim in this file.
REMIT_ADJUSTMENT_CODES = {
    "WO": "Overpayment recovery",
    "L6": "Interest owed",
    "FB": "Forwarding balance",
}


def code_label(group_code: str, reason_code: str) -> str:
    return f"{group_code}-{reason_code}"


def describe(reason_code: str) -> str:
    return REASON_CODES.get(reason_code, f"Reason {reason_code}")


def is_patient_responsibility(group_code: str) -> bool:
    return group_code == "PR"


def is_denial(group_code: str, reason_code: str) -> bool:
    return group_code != "PR" and reason_code in DENIAL_REASONS
