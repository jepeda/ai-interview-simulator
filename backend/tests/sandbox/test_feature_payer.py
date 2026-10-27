"""Sandbox feature: filter the weekly card by payer."""

from fastapi.testclient import TestClient

from sandbox.main import app

client = TestClient(app)


def test_filters_lines_and_total_by_payer():
    res = client.get("/providers/1/week", params={"start": "2026-10-19", "payer": "Aetna"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert [line["session_id"] for line in body["lines"]] == [1, 6]
    assert body["total_cents"] == 33000
    assert body["payer"] == "Aetna"


def test_payer_match_ignores_case():
    res = client.get("/providers/1/week", params={"start": "2026-10-19", "payer": "self-PAY"})
    assert res.status_code == 200, res.text
    assert res.json()["total_cents"] == 22000


def test_unknown_payer_is_rejected():
    res = client.get("/providers/1/week", params={"start": "2026-10-19", "payer": "Blue Shield"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "unknown_payer"
