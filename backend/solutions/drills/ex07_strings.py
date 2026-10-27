"""Drill 07 - Strings and f-strings (reference solution)."""


def format_member_id(raw: str) -> str:
    cleaned = raw.strip().upper().replace(" ", "").replace("-", "")
    return "-".join(cleaned[i : i + 3] for i in range(0, len(cleaned), 3))


def initials(full_name: str) -> str:
    return "".join(f"{part[0].upper()}." for part in full_name.split())


def format_money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


def mrn(n: int) -> str:
    return f"MRN-{n:06d}"
