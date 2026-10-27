"""In-memory demo data: one provider's client invoices (Sep-Oct 2026)."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Provider:
    id: int
    name: str


@dataclass(frozen=True)
class Invoice:
    id: int
    provider_id: int
    client_name: str
    service_date: date
    allowed_cents: int
    copay_cents: int | None  # flat copay, or None when the plan uses coinsurance
    coinsurance_pct: int | None  # e.g. 20 for 20%
    paid_cents: int
    status: str  # open | paid | written_off


PROVIDERS = [Provider(1, "Jordan Lee, LCSW")]

INVOICES = [
    Invoice(101, 1, "Chen, Mei", date(2026, 9, 8), 13333, None, 20, 0, "open"),
    Invoice(102, 1, "Patel, Arjun", date(2026, 9, 15), 15000, 3000, None, 0, "open"),
    Invoice(103, 1, "Garcia, Sofia", date(2026, 9, 22), 17499, None, 20, 1000, "open"),
    Invoice(104, 1, "Okafor, Ngozi", date(2026, 10, 1), 51117, None, 30, 0, "open"),
    Invoice(105, 1, "Kim, Daniel", date(2026, 10, 6), 15000, 2500, None, 2500, "open"),
    Invoice(106, 1, "Rossi, Luca", date(2026, 10, 13), 45833, None, 20, 0, "open"),
    Invoice(107, 1, "Novak, Eva", date(2026, 10, 20), 16500, 4000, None, 4000, "paid"),
    Invoice(108, 1, "Brown, Tyler", date(2026, 8, 11), 16500, 3500, None, 0, "written_off"),
]
