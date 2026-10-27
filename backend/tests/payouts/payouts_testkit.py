"""Shared constants and helpers for the payouts tests (fixtures are in conftest.py)."""

from fastapi.testclient import TestClient

RATE_90837 = 16500  # Aetna 60-minute session, for every test provider
RATE_90834 = 13000  # Aetna 45-minute session
LATE_CANCEL_FEE = 7500


def statement(client: TestClient, provider, period_start: str) -> dict:
    response = client.get(f"/providers/{provider.id}/statements/{period_start}")
    assert response.status_code == 200, response.text
    return response.json()


def appointment_ids(body: dict) -> list[int]:
    return [line["appointment_id"] for line in body["lines"]]
