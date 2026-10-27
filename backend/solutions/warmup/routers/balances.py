from datetime import date

from fastapi import APIRouter

from warmup.data import PROVIDERS
from warmup.services.balances import balances_report

router = APIRouter(tags=["balances"])


@router.get("/providers")
def list_providers() -> list[dict]:
    return [{"id": p.id, "name": p.name} for p in PROVIDERS]


@router.get("/providers/{provider_id}/balances")
def get_balances(provider_id: int, as_of: date | None = None, min_balance_cents: int = 0) -> dict:
    return balances_report(provider_id, as_of, min_balance_cents)
