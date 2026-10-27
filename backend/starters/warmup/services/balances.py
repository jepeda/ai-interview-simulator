"""Outstanding patient balances for a provider's practice."""

from warmup.data import INVOICES, PROVIDERS, Invoice, Provider
from warmup.errors import NotFound
from warmup.money import percent_of


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


def balances_report(provider_id: int) -> dict:
    provider = get_provider(provider_id)
    lines = []
    for invoice in sorted(INVOICES, key=lambda i: (i.service_date, i.id)):
        if invoice.provider_id != provider.id or invoice.status != "open":
            continue
        owed = patient_responsibility(invoice)
        balance = owed - invoice.paid_cents
        if balance <= 0:
            continue
        lines.append(
            {
                "invoice_id": invoice.id,
                "client_name": invoice.client_name,
                "service_date": invoice.service_date,
                "responsibility_cents": owed,
                "paid_cents": invoice.paid_cents,
                "balance_cents": balance,
            }
        )
    return {
        "provider": {"id": provider.id, "name": provider.name},
        "lines": lines,
        "total_cents": sum(line["balance_cents"] for line in lines),
    }
