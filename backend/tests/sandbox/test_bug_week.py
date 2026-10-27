"""Sandbox ticket: the weekly earnings card overpays (see the interview ticket)."""

from fastapi.testclient import TestClient

from sandbox.main import app

client = TestClient(app)


def week() -> dict:
    res = client.get("/providers/1/week", params={"start": "2026-10-19"})
    assert res.status_code == 200, res.text
    return res.json()


def test_week_total_matches_finance():
    assert week()["total_cents"] == 76000


def test_late_cancel_pays_the_flat_fee():
    late = [line for line in week()["lines"] if line["status"] == "late_cancel"]
    assert [line["amount_cents"] for line in late] == [7500]


def test_no_shows_and_cancellations_are_not_on_the_card():
    assert {line["status"] for line in week()["lines"]} == {"completed", "late_cancel"}
    assert [line["session_id"] for line in week()["lines"]] == [1, 2, 3, 4, 6]


def test_week_must_start_on_monday():
    res = client.get("/providers/1/week", params={"start": "2026-10-20"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_week"
