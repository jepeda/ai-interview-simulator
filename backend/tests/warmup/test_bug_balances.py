"""Warmup ticket: outstanding balances are off by a few cents (see the interview ticket)."""

from fastapi.testclient import TestClient

from warmup.main import app
from warmup.money import percent_of

client = TestClient(app)


def report() -> dict:
    res = client.get("/providers/1/balances")
    assert res.status_code == 200, res.text
    return res.json()


def balances() -> dict[int, int]:
    return {line["invoice_id"]: line["balance_cents"] for line in report()["lines"]}


def test_total_matches_the_billing_export():
    assert report()["total_cents"] == 32669


def test_coinsurance_rounds_to_the_nearest_cent():
    assert balances()[101] == 2667  # 20% of $133.33 = $26.666
    assert balances()[106] == 9167  # 20% of $458.33 = $91.666
    assert balances()[103] == 2500  # 20% of $174.99 = $34.998, minus $10.00 paid


def test_half_a_cent_rounds_up():
    assert percent_of(12345, 10) == 1235  # $12.345
    assert percent_of(10, 25) == 3  # 2.5 cents
    assert percent_of(51117, 30) == 15335  # $153.351 rounds down


def test_only_open_invoices_with_a_balance():
    assert sorted(balances()) == [101, 102, 103, 104, 106]
