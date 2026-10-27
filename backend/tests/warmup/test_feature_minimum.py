"""Warmup feature: only balances worth a follow-up call."""

from fastapi.testclient import TestClient

from warmup.main import app

client = TestClient(app)


def test_filters_lines_and_total_by_minimum_balance():
    res = client.get("/providers/1/balances", params={"min_balance_cents": 3000})
    assert res.status_code == 200, res.text
    body = res.json()
    assert [line["invoice_id"] for line in body["lines"]] == [102, 104, 106]
    assert body["total_cents"] == 27502


def test_minimum_is_inclusive_and_defaults_to_everything():
    res = client.get("/providers/1/balances", params={"min_balance_cents": 2667})
    assert [line["invoice_id"] for line in res.json()["lines"]] == [101, 102, 104, 106]
    assert len(client.get("/providers/1/balances").json()["lines"]) == 5


def test_negative_minimum_is_rejected():
    res = client.get("/providers/1/balances", params={"min_balance_cents": -1})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_min_balance"
