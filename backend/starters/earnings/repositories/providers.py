from sqlalchemy import select
from sqlalchemy.orm import Session

from earnings.errors import NotFound
from earnings.models import Provider


def list_providers(db: Session) -> list[Provider]:
    return list(db.scalars(select(Provider).order_by(Provider.name)))


def get_provider(db: Session, provider_id: int) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise NotFound(f"Provider {provider_id} not found", code="provider_not_found")
    return provider
