"""Drill 09 - Filtering, searching and generator expressions (reference solution)."""

from datetime import date


def find_patient(patients: list[dict], patient_id: int) -> dict | None:
    return next((p for p in patients if p["id"] == patient_id), None)


def all_claims_verified(claims: list[dict]) -> bool:
    return all(claim["verified"] for claim in claims)


def has_overdue_invoice(invoices: list[dict], today: date) -> bool:
    return any(not inv["paid"] and inv["due"] < today for inv in invoices)


def billable_minutes(sessions: list[dict]) -> int:
    return sum(
        s["minutes"]
        for s in sessions
        if s["status"] == "completed" and s["minutes"] >= 30 and not s["billed"]
    )
