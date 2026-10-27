"""Feature: a denial work queue with aging buckets (GET /denials)."""

from datetime import date, timedelta

import pytest
from remits_testkit import era, line, post_era
from sqlalchemy.orm import Session

from remits.seed import seed

TODAY = date(2026, 10, 26)
EMPTY = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}


def denied(claim_number: str, reason: str = "197", billed: str = "200.00") -> dict:
    return line(claim_number, billed, "0.00", ("CO", reason, billed), status="4")


def get_denials(client, **params) -> dict:
    response = client.get("/denials", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_denied_claim_is_in_the_queue(client, make_claim, set_today):
    set_today(TODAY)
    make_claim("HW-1", date_of_service=date(2026, 8, 17), patient_name="Okoro, Chidi")
    post_era(client, era(denied("HW-1", "197"), paid_on="2026-10-06"))

    body = get_denials(client)

    assert body["as_of"] == "2026-10-26"
    assert body["buckets"] == EMPTY | {"61-90": 1}
    [item] = body["claims"]
    assert item["claim_number"] == "HW-1"
    assert item["patient_name"] == "Okoro, Chidi"
    assert item["payer"] == "Aetna"
    assert item["billed_cents"] == 20000
    assert item["denial_code"] == "CO-197"
    assert item["denial_reason"] == "Precertification/authorization absent"
    assert item["denied_on"] == "2026-10-06"
    assert item["days_outstanding"] == 70  # counted from the date of service
    assert item["bucket"] == "61-90"


@pytest.mark.parametrize(
    ("days", "bucket"),
    [(0, "0-30"), (30, "0-30"), (31, "31-60"), (60, "31-60"), (61, "61-90"), (90, "61-90"), (91, "90+"), (400, "90+")],
)
def test_aging_bucket_boundaries(client, make_claim, set_today, days, bucket):
    set_today(TODAY)
    make_claim("HW-1", date_of_service=TODAY - timedelta(days=days))
    post_era(client, era(denied("HW-1")))

    [item] = get_denials(client)["claims"]

    assert (item["days_outstanding"], item["bucket"]) == (days, bucket)


def test_only_denied_claims_are_listed(client, make_claim, set_today):
    set_today(TODAY)
    make_claim("HW-PAID")
    make_claim("HW-DEDUCTIBLE")  # nothing paid, but it's the client's deductible: not a denial
    make_claim("HW-DENIED")
    make_claim("HW-UNPOSTED")
    make_claim("HW-LATER-PAID")
    post_era(
        client,
        era(
            line("HW-PAID", "200.00", "138.17", ("CO", "45", "31.83"), ("PR", "3", "30.00")),
            line("HW-DEDUCTIBLE", "200.00", "0.00", ("CO", "45", "31.83"), ("PR", "1", "168.17")),
            denied("HW-DENIED", "16"),
            denied("HW-LATER-PAID", "16"),
            trace="1000000001",
        ),
    )
    # The corrected claim was paid on a later remit (reversal of the denial + payment).
    post_era(
        client,
        era(
            line("HW-LATER-PAID", "0.00", "138.17", ("CO", "16", "-200.00"), ("CO", "45", "31.83"), ("PR", "3", "30.00")),
            trace="1000000002",
        ),
    )

    body = get_denials(client)

    assert [c["claim_number"] for c in body["claims"]] == ["HW-DENIED"]
    assert sum(body["buckets"].values()) == 1


def test_oldest_first_and_filters(client, make_claim, set_today):
    set_today(TODAY)
    make_claim("HW-1", payer="Aetna", date_of_service=date(2026, 10, 1))
    make_claim("HW-2", payer="Aetna", date_of_service=date(2026, 7, 14))
    make_claim("HW-3", payer="Cigna", date_of_service=date(2026, 9, 15))
    make_claim("HW-4", payer="Cigna", date_of_service=date(2026, 9, 15))
    post_era(client, era(denied("HW-1", "197"), denied("HW-2", "29"), payer="Aetna", trace="A1"))
    post_era(client, era(denied("HW-4", "16"), denied("HW-3", "197"), payer="Cigna", trace="C1"))

    everything = get_denials(client)
    assert [c["claim_number"] for c in everything["claims"]] == ["HW-2", "HW-3", "HW-4", "HW-1"]
    assert everything["buckets"] == {"0-30": 1, "31-60": 2, "61-90": 0, "90+": 1}

    cigna = get_denials(client, payer="cigna")
    assert [c["claim_number"] for c in cigna["claims"]] == ["HW-3", "HW-4"]
    assert cigna["buckets"] == EMPTY | {"31-60": 2}

    no_auth = get_denials(client, code="CO-197")
    assert [c["claim_number"] for c in no_auth["claims"]] == ["HW-3", "HW-1"]
    assert get_denials(client, payer="Optum")["claims"] == []


def test_seeded_denials(client, db: Session, set_today):
    seed(db)
    set_today(TODAY)

    body = get_denials(client)

    assert [(c["claim_number"], c["denial_code"], c["bucket"]) for c in body["claims"]] == [
        ("HW-1028", "CO-29", "90+"),
        ("HW-1036", "CO-197", "61-90"),
        ("HW-1032", "CO-16", "31-60"),
        ("HW-1046", "CO-197", "0-30"),
    ]
