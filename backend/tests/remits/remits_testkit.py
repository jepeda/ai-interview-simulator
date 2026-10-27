"""Shared constants and helpers for the remits tests (fixtures are in conftest.py).

ERA payloads are built the way the clearinghouse sends them: amounts as dollar strings.
"""

from decimal import Decimal

from fastapi.testclient import TestClient

BILLED = {"90791": 25000, "90834": 18000, "90837": 20000}


def line(
    claim_number: str,
    billed: str = "200.00",
    paid: str = "100.00",
    *adjustments: tuple[str, str, str],
    status: str = "1",
) -> dict:
    """One claim line. Adjustments are (group, reason, amount), e.g. ("CO", "45", "70.00")."""
    if not adjustments and Decimal(billed) != Decimal(paid):
        adjustments = (("CO", "45", str(Decimal(billed) - Decimal(paid))),)
    return {
        "claim_number": claim_number,
        "status_code": status,
        "billed": billed,
        "paid": paid,
        "adjustments": [{"group": g, "reason": r, "amount": a} for g, r, a in adjustments],
    }


def era(
    *lines: dict,
    payer: str = "Aetna",
    trace: str = "1000000001",
    paid_on: str = "2026-10-09",
    remit_adjustments: list[dict] | None = None,
    total: str | None = None,
) -> dict:
    """A whole ERA. `total` defaults to the sum of the lines' paid amounts + remit adjustments."""
    remit_adjustments = remit_adjustments or []
    if total is None:
        total = str(
            sum((Decimal(item["paid"]) for item in lines), Decimal("0"))
            + sum((Decimal(a["amount"]) for a in remit_adjustments), Decimal("0"))
        )
    return {
        "payer": payer,
        "trace_number": trace,
        "payment_method": "ACH",
        "paid_on": paid_on,
        "total_paid": total,
        "claims": list(lines),
        "remit_adjustments": remit_adjustments,
    }


def post_era(client: TestClient, payload: dict, expect: int = 201) -> dict:
    response = client.post("/remittances", json=payload)
    assert response.status_code == expect, response.text
    return response.json()


def get_claim(client: TestClient, claim_number: str) -> dict:
    response = client.get(f"/claims/{claim_number}")
    assert response.status_code == 200, response.text
    return response.json()


def get_remittances(client: TestClient) -> list[dict]:
    response = client.get("/remittances")
    assert response.status_code == 200, response.text
    return response.json()
