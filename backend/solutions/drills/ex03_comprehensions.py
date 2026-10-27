"""Drill 03 - Comprehensions (reference solution)."""


def active_emails(patients: list[dict]) -> list[str]:
    return [
        p["email"].strip().lower()
        for p in patients
        if p["status"] == "active" and p["email"] is not None
    ]


def index_by_id(patients: list[dict]) -> dict[int, dict]:
    return {p["id"]: p for p in patients}


def unique_payers(plans: list[dict]) -> list[str]:
    return sorted({plan["payer"] for plan in plans})


def flatten_diagnoses(visits: list[dict]) -> list[str]:
    return [code for visit in visits for code in visit["codes"]]
