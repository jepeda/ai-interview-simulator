"""Drill 06 - None handling and truthiness (reference solution)."""


def display_copay(copay_cents: int | None) -> str:
    if copay_cents is None:
        return "Unknown"
    return f"${copay_cents / 100:,.2f}"


def primary_phone(patient: dict) -> str | None:
    contact = patient.get("contact") or {}
    phones = contact.get("phones") or []
    if not phones:
        return None
    return (phones[0] or {}).get("number")


def first_present(*values: str | None) -> str | None:
    return next((value for value in values if value is not None), None)


def member_id_or_self_pay(patient: dict) -> str:
    member_id = (patient.get("member_id") or "").strip()
    return member_id or "SELF-PAY"
