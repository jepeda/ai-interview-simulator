"""Outstanding patient balances for a provider's practice."""

from datetime import date

from warmup.data import INVOICES, PROVIDERS, Invoice, Provider
from warmup.errors import InvalidRequest, NotFound
from warmup.money import percent_of

BUCKETS = ["0-30", "31-60", "61-90", "90+"]


def get_provider(provider_id: int) -> Provider:
    provider = next((p for p in PROVIDERS if p.id == provider_id), None)
    if provider is None:
        raise NotFound(f"Provider {provider_id} not found")
    return provider


def patient_responsibility(invoice: Invoice) -> int:
    """What the client owes for the session, in cents: their copay or their coinsurance share."""
    if invoice.copay_cents is not None:
        return invoice.copay_cents
    return percent_of(invoice.allowed_cents, invoice.coinsurance_pct or 0)


def aging_bucket(days: int) -> str:
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def balances_report(provider_id: int, as_of: date | None = None, min_balance_cents: int = 0) -> dict:
    provider = get_provider(provider_id)
    if min_balance_cents < 0:
        raise InvalidRequest("min_balance_cents can't be negative", code="invalid_min_balance")
    as_of = as_of or date.today()
    lines = []
    for invoice in sorted(INVOICES, key=lambda i: (i.service_date, i.id)):
        if invoice.provider_id != provider.id or invoice.status != "open":
            continue
        owed = patient_responsibility(invoice)
        balance = owed - invoice.paid_cents
        if balance <= 0 or balance < min_balance_cents:
            continue
        days = max(0, (as_of - invoice.service_date).days)
        lines.append(
            {
                "invoice_id": invoice.id,
                "client_name": invoice.client_name,
                "service_date": invoice.service_date,
                "responsibility_cents": owed,
                "paid_cents": invoice.paid_cents,
                "balance_cents": balance,
                "days_outstanding": days,
                "bucket": aging_bucket(days),
            }
        )
    buckets = dict.fromkeys(BUCKETS, 0)
    for line in lines:
        buckets[line["bucket"]] += line["balance_cents"]
    return {
        "provider": {"id": provider.id, "name": provider.name},
        "as_of": as_of,
        "lines": lines,
        "buckets": buckets,
        "total_cents": sum(line["balance_cents"] for line in lines),
    }
