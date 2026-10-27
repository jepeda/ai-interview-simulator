"""The weekly earnings card: what a provider is paid for the sessions in one Monday-Sunday week."""

from datetime import date, timedelta

from sandbox.data import (
    LATE_CANCEL_FEE_CENTS,
    PAYERS,
    PROVIDERS,
    RATES_CENTS,
    SESSIONS,
    Provider,
    Session,
)
from sandbox.errors import InvalidRequest, NotFound

PAID_STATUSES = {"completed", "late_cancel"}


def get_provider(provider_id: int) -> Provider:
    provider = next((p for p in PROVIDERS if p.id == provider_id), None)
    if provider is None:
        raise NotFound(f"Provider {provider_id} not found")
    return provider


def session_amount(session: Session) -> int:
    """What one session pays the provider, in cents."""
    if session.status == "late_cancel":
        return LATE_CANCEL_FEE_CENTS
    if session.status == "completed":
        return RATES_CENTS[session.cpt_code]
    return 0


def _payer_name(payer: str) -> str:
    match = next((p for p in PAYERS if p.lower() == payer.strip().lower()), None)
    if match is None:
        raise InvalidRequest(f"Unknown payer {payer!r}", code="unknown_payer")
    return match


def week_card(provider_id: int, start: date, payer: str | None = None) -> dict:
    provider = get_provider(provider_id)
    if start.weekday() != 0:
        raise InvalidRequest(f"{start.isoformat()} is not a Monday", code="invalid_week")
    payer_name = _payer_name(payer) if payer else None
    end = start + timedelta(days=6)
    sessions = [
        s
        for s in SESSIONS
        if s.provider_id == provider.id
        and start <= s.day <= end
        and s.status in PAID_STATUSES
        and (payer_name is None or s.payer == payer_name)
    ]
    lines = [
        {
            "session_id": s.id,
            "date": s.day,
            "client_name": s.client_name,
            "cpt_code": s.cpt_code,
            "payer": s.payer,
            "status": s.status,
            "amount_cents": session_amount(s),
        }
        for s in sorted(sessions, key=lambda s: (s.day, s.id))
    ]
    return {
        "provider": {"id": provider.id, "name": provider.name},
        "week_start": start,
        "week_end": end,
        "payer": payer_name,
        "lines": lines,
        "total_cents": sum(line["amount_cents"] for line in lines),
    }
