"""Warmup feature: aging buckets."""

from fastapi.testclient import TestClient

from warmup.main import app

client = TestClient(app)


def report(**params) -> dict:
    res = client.get("/providers/1/balances", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def test_days_outstanding_and_bucket_per_line():
    lines = {line["invoice_id"]: line for line in report(as_of="2026-10-26")["lines"]}
    assert (lines[101]["days_outstanding"], lines[101]["bucket"]) == (48, "31-60")
    assert (lines[104]["days_outstanding"], lines[104]["bucket"]) == (25, "0-30")
    assert (lines[102]["days_outstanding"], lines[102]["bucket"]) == (41, "31-60")


def test_bucket_totals_include_every_bucket():
    body = report(as_of="2026-12-10")
    assert body["buckets"] == {"0-30": 0, "31-60": 9167, "61-90": 20835, "90+": 2667}
    assert sum(body["buckets"].values()) == body["total_cents"]


def test_boundaries_are_inclusive_at_the_top():
    lines = {line["invoice_id"]: line for line in report(as_of="2026-10-08")["lines"]}
    assert (lines[101]["days_outstanding"], lines[101]["bucket"]) == (30, "0-30")
    lines = {line["invoice_id"]: line for line in report(as_of="2026-10-09")["lines"]}
    assert lines[101]["bucket"] == "31-60"
