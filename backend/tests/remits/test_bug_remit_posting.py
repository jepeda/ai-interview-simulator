"""Support ticket #6243: a re-delivered ERA, penny balances, and a recoupment shown wrong.

A payment is identified by its payer + trace number (TRN02). Money is integer cents end to end.
"""

import pytest
from remits_testkit import era, get_claim, get_remittances, line, post_era
from sqlalchemy.orm import Session

from remits.seed import seed


def test_redelivered_era_is_posted_once(client, make_claim):
    make_claim("HW-1", payer="Optum")
    payload = era(line("HW-1", "200.00", "100.00"), payer="Optum", trace="1102948731")

    first = post_era(client, payload)
    replay = client.post("/remittances", json=payload)

    assert replay.status_code in (200, 201, 409), replay.text
    if replay.status_code != 409:
        assert replay.json()["id"] == first["id"]  # the same payment, not a new one
    assert len(get_remittances(client)) == 1
    claim = get_claim(client, "HW-1")
    assert len(claim["payments"]) == 1
    assert (claim["paid_cents"], claim["balance_cents"], claim["status"]) == (10000, 0, "paid")


def test_redelivery_with_a_padded_trace_number_is_still_the_same_payment(client, make_claim):
    make_claim("HW-1", payer="Optum")
    post_era(client, era(line("HW-1"), payer="Optum", trace="1102948731"))

    client.post("/remittances", json=era(line("HW-1"), payer="Optum", trace="1102948731  "))

    assert len(get_remittances(client)) == 1
    assert get_claim(client, "HW-1")["paid_cents"] == 10000


def test_same_trace_number_from_another_payer_is_a_different_payment(client, make_claim):
    make_claim("HW-1", payer="Aetna")
    make_claim("HW-2", payer="Cigna")

    post_era(client, era(line("HW-1"), payer="Aetna", trace="004417920"))
    post_era(client, era(line("HW-2"), payer="Cigna", trace="004417920"))

    assert len(get_remittances(client)) == 2
    assert get_claim(client, "HW-1")["paid_cents"] == 10000
    assert get_claim(client, "HW-2")["paid_cents"] == 10000


def test_different_payments_for_the_same_claim_all_post(client, make_claim):
    """Paid, reversed (CLP02 = 22), then paid again: three real payments with different traces."""
    make_claim("HW-1")
    paid = line("HW-1", "200.00", "100.00")
    reversal = line("HW-1", "-200.00", "-100.00", ("CO", "45", "-100.00"), status="22")

    post_era(client, era(paid, trace="1000000001"))
    post_era(client, era(reversal, trace="1000000002"))
    post_era(client, era(paid, trace="1000000003"))

    claim = get_claim(client, "HW-1")
    assert len(claim["payments"]) == 3
    assert (claim["paid_cents"], claim["balance_cents"]) == (10000, 0)


def test_dollar_amounts_post_as_exact_cents(client, make_claim):
    make_claim("HW-1")
    post_era(client, era(line("HW-1", "200.00", "138.17", ("CO", "45", "31.83"), ("PR", "3", "30.00"))))

    claim = get_claim(client, "HW-1")

    assert claim["paid_cents"] == 13817
    assert claim["adjusted_cents"] == 3183
    assert claim["patient_resp_cents"] == 3000
    assert (claim["balance_cents"], claim["status"]) == (0, "paid")


@pytest.mark.parametrize(
    ("amount", "cents"),
    [("0.29", 29), ("1.15", 115), ("4.35", 435), ("137.17", 13717), ("1234.56", 123456), ("19.9", 1990), ("25", 2500)],
)
def test_every_amount_converts_exactly(client, make_claim, amount, cents):
    make_claim("HW-1", cpt_code="90791")
    posted = post_era(client, era(line("HW-1", "250.00", amount)))

    assert posted["total_paid_cents"] == cents
    assert posted["lines"][0]["paid_cents"] == cents
    assert posted["out_of_balance_cents"] == 0
    assert get_claim(client, "HW-1")["balance_cents"] == 0


def test_negative_amounts_convert_exactly(client, make_claim):
    make_claim("HW-1")
    post_era(client, era(line("HW-1", "200.00", "137.17"), trace="1000000001"))

    reversal = post_era(
        client, era(line("HW-1", "-200.00", "-137.17", ("CO", "45", "-62.83"), status="22"), trace="1000000002")
    )

    assert reversal["total_paid_cents"] == -13717
    assert reversal["out_of_balance_cents"] == 0
    claim = get_claim(client, "HW-1")
    assert (claim["paid_cents"], claim["adjusted_cents"], claim["balance_cents"]) == (0, 0, 20000)


def test_remittance_with_a_recoupment_balances(client, make_claim):
    make_claim("HW-1")
    make_claim("HW-2")
    posted = post_era(
        client,
        era(
            line("HW-1", "200.00", "138.17", ("CO", "45", "31.83"), ("PR", "3", "30.00")),
            line("HW-2", "200.00", "137.17", ("CO", "45", "37.83"), ("PR", "3", "25.00")),
            remit_adjustments=[{"code": "WO", "reference": "HW-0987", "amount": "-42.15"}],
        ),
    )

    assert posted["total_paid_cents"] == 13817 + 13717 - 4215
    assert posted["posted_cents"] == posted["total_paid_cents"]
    assert posted["out_of_balance_cents"] == 0
    assert posted["remit_adjustments"][0]["amount_cents"] == -4215


def test_ticket_data_matches_the_eobs(client, db: Session):
    """The seeded ERAs from the ticket, replayed in delivery order (incl. Optum's re-send)."""
    seed(db)

    hw_1042 = get_claim(client, "HW-1042")
    assert len(hw_1042["payments"]) == 1
    assert (hw_1042["paid_cents"], hw_1042["balance_cents"], hw_1042["status"]) == (13717, 0, "paid")
    for number in ("HW-1029", "HW-1030", "HW-1041", "HW-1043", "HW-1044"):
        claim = get_claim(client, number)
        assert (claim["balance_cents"], claim["status"]) == (0, "paid"), number

    remits = get_remittances(client)
    optum = [r for r in remits if r["payer"] == "Optum"]
    assert len(optum) == 1
    assert optum[0]["total_paid_cents"] == optum[0]["posted_cents"] == 59439
    assert all(r["out_of_balance_cents"] == 0 for r in remits)
