"""In-memory demo data: one provider's sessions for the week of Mon Oct 19, 2026."""

from dataclasses import dataclass
from datetime import date

LATE_CANCEL_FEE_CENTS = 7500

# Contracted rate per CPT code, in cents.
RATES_CENTS = {"90791": 22000, "90834": 13500, "90837": 16500}

PAYERS = ["Aetna", "Cigna", "Optum", "Self-pay"]


@dataclass(frozen=True)
class Provider:
    id: int
    name: str


@dataclass(frozen=True)
class Session:
    id: int
    provider_id: int
    day: date
    client_name: str
    cpt_code: str
    payer: str
    status: str  # completed | late_cancel | no_show | cancelled


PROVIDERS = [Provider(1, "Dr. Sam Rivera, PsyD")]

SESSIONS = [
    Session(1, 1, date(2026, 10, 19), "Nguyen, Linh", "90837", "Aetna", "completed"),
    Session(2, 1, date(2026, 10, 20), "Brooks, Tamara", "90834", "Cigna", "completed"),
    Session(3, 1, date(2026, 10, 21), "Alvarez, Diego", "90837", "Optum", "late_cancel"),
    Session(4, 1, date(2026, 10, 22), "Kowalski, Erin", "90791", "Self-pay", "completed"),
    Session(5, 1, date(2026, 10, 23), "Okoro, Chidi", "90834", "Aetna", "no_show"),
    Session(6, 1, date(2026, 10, 23), "Nguyen, Linh", "90837", "Aetna", "completed"),
    Session(7, 1, date(2026, 10, 24), "Reyes, Marisol", "90834", "Cigna", "cancelled"),
    Session(8, 1, date(2026, 10, 26), "Brooks, Tamara", "90834", "Cigna", "completed"),  # next week
]
