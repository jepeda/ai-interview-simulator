from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from payouts.db import get_db
from payouts.repositories import providers as providers_repo
from payouts.schemas import ProviderOut

router = APIRouter(prefix="/providers", tags=["providers"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[ProviderOut])
def list_providers(db: DbSession) -> list[ProviderOut]:
    return [ProviderOut.model_validate(p) for p in providers_repo.list_providers(db)]


@router.get("/{provider_id}", response_model=ProviderOut)
def get_provider(db: DbSession, provider_id: int) -> ProviderOut:
    return ProviderOut.model_validate(providers_repo.get_provider(db, provider_id))
