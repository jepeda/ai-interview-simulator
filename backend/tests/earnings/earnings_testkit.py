"""Shared constants and helpers for the earnings tests (fixtures are in conftest.py)."""

from datetime import date

from fastapi.testclient import TestClient

TODAY = date(2026, 10, 23)  # what get_today returns in tests, unless a test overrides it


def get_json(client: TestClient, path: str) -> dict | list:
    response = client.get(path)
    assert response.status_code == 200, response.text
    return response.json()


def month(client: TestClient, provider, month_key: str) -> dict:
    return get_json(client, f"/providers/{provider.id}/earnings/{month_key}")


def summary(client: TestClient, provider, year: int = 2026) -> dict:
    return get_json(client, f"/providers/{provider.id}/earnings?year={year}")


def rate_card(client: TestClient, provider) -> dict[tuple[str, str], dict]:
    rows = get_json(client, f"/providers/{provider.id}/rate-card")
    return {(row["payer"], row["cpt_code"]): row for row in rows}


def rates_by_date(body: dict) -> dict[str, int]:
    """{service_date: rate_cents} for a month-detail response."""
    return {line["service_date"]: line["rate_cents"] for line in body["lines"]}
