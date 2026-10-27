"""Feature: a negative balance is never paid out; it carries into the next period."""

from datetime import date

from payouts_testkit import RATE_90837, statement


def carryovers(body: dict) -> list[dict]:
    return [a for a in body["adjustments"] if a["reason"].startswith("Carryover from")]


def test_negative_period_pays_zero(client, make_provider, make_appointment, make_adjustment):
    provider = make_provider()
    make_appointment(provider, "2026-10-20 10:00")
    make_adjustment(provider, date(2026, 10, 21), -50000, "Recoupment: payer audit")

    body = statement(client, provider, "2026-10-16")

    assert body["total_cents"] == RATE_90837 - 50000
    assert body["payout_cents"] == 0


def test_positive_period_pays_its_total(client, make_provider, make_appointment):
    provider = make_provider()
    make_appointment(provider, "2026-10-20 10:00")

    body = statement(client, provider, "2026-10-16")

    assert body["payout_cents"] == body["total_cents"] == RATE_90837
    assert carryovers(body) == []


def test_negative_balance_carries_into_the_next_period(client, make_provider, make_appointment, make_adjustment):
    provider = make_provider()
    make_appointment(provider, "2026-10-20 10:00")
    make_adjustment(provider, date(2026, 10, 21), -20000, "Recoupment: payer audit")  # net -3500
    make_appointment(provider, "2026-11-03 10:00")
    make_appointment(provider, "2026-11-04 10:00")

    november = statement(client, provider, "2026-11-01")

    [carry] = carryovers(november)
    assert carry["amount_cents"] == RATE_90837 - 20000
    assert "2026-10-16" in carry["reason"]  # says which period it came from
    assert november["total_cents"] == 2 * RATE_90837 + (RATE_90837 - 20000)
    assert november["payout_cents"] == november["total_cents"]


def test_carryover_chains_across_periods(client, make_provider, make_appointment, make_adjustment):
    provider = make_provider()
    make_adjustment(provider, date(2026, 10, 20), -100000, "Recoupment: payer audit")  # -1000.00
    make_appointment(provider, "2026-11-03 10:00")  # Nov 1-15: 165.00 - 1000.00 = -835.00
    make_appointment(provider, "2026-11-17 10:00")  # Nov 16-30: 165.00 - 835.00 = -670.00
    for day in range(1, 6):
        make_appointment(provider, f"2026-12-0{day} 10:00")  # Dec 1-15: 825.00 - 670.00

    nov1 = statement(client, provider, "2026-11-01")
    nov16 = statement(client, provider, "2026-11-16")
    dec1 = statement(client, provider, "2026-12-01")

    assert (nov1["total_cents"], nov1["payout_cents"]) == (RATE_90837 - 100000, 0)
    assert carryovers(nov16)[0]["amount_cents"] == RATE_90837 - 100000
    assert (nov16["total_cents"], nov16["payout_cents"]) == (2 * RATE_90837 - 100000, 0)
    assert carryovers(dec1)[0]["amount_cents"] == 2 * RATE_90837 - 100000
    assert dec1["total_cents"] == dec1["payout_cents"] == 7 * RATE_90837 - 100000


def test_carryover_is_counted_once(client, make_provider, make_appointment, make_adjustment):
    """A balance that was paid back must not keep carrying forward."""
    provider = make_provider()
    make_adjustment(provider, date(2026, 10, 20), -20000, "Recoupment")
    make_appointment(provider, "2026-11-03 10:00")  # 165.00 - 200.00 = -35.00
    make_appointment(provider, "2026-11-17 10:00")  # 165.00 - 35.00 = 130.00 (paid)
    make_appointment(provider, "2026-12-02 10:00")  # 165.00, nothing carried

    dec1 = statement(client, provider, "2026-12-01")

    assert carryovers(dec1) == []
    assert dec1["payout_cents"] == RATE_90837
