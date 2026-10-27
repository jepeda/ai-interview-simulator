from datetime import date

from fastapi import APIRouter

from sandbox.data import PROVIDERS
from sandbox.services.earnings import week_card

router = APIRouter(tags=["earnings"])


@router.get("/providers")
def list_providers() -> list[dict]:
    return [{"id": p.id, "name": p.name} for p in PROVIDERS]


@router.get("/providers/{provider_id}/week")
def get_week(provider_id: int, start: date) -> dict:
    return week_card(provider_id, start)
