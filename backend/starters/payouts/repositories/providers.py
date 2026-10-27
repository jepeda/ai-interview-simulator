from sqlalchemy import select
from sqlalchemy.orm import Session

from payouts.errors import NotFound
from payouts.models import FeeSchedule, Provider


def list_providers(db: Session) -> list[Provider]:
    return list(db.scalars(select(Provider).order_by(Provider.name)))


def get_provider(db: Session, provider_id: int) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise NotFound(f"Provider {provider_id} not found", code="provider_not_found")
    return provider


def fee_table(db: Session, provider_id: int) -> dict[tuple[str, str], int]:
    """{(payer, cpt_code): rate_cents} for one provider."""
    rows = db.scalars(select(FeeSchedule).where(FeeSchedule.provider_id == provider_id))
    return {(row.payer, row.cpt_code): row.rate_cents for row in rows}
