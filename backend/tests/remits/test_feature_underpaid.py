"""Feature: flag claims the payer allowed for less than our contract (GET /underpayments)."""

from decimal import Decimal

import pytest
from remits_testkit import era, line, post_era
from sqlalchemy.orm import Session

from remits.seed import seed

CONTRACT_90837 = 16817  # Aetna, in these tests


def paid(claim_number: str, allowed: str, copay: str = "30.00") -> dict:
    """A clean 835 line for a 90837 billed at $200.00, allowed `allowed`, with a copay."""
    payer_paid = Decimal(allowed) - Decimal(copay)
    write_off = Decimal("200.00") - Decimal(allowed)
    return line(claim_number, "200.00", str(payer_paid), ("CO", "45", str(write_off)), ("PR", "3", copay))


def get_report(client) -> dict:
    response = client.get("/underpayments")
    assert response.status_code == 200, response.text
    return response.json()


def test_claim_allowed_below_contract_is_flagged(client, make_claim, make_fee):
    make_fee("Aetna", "90837", CONTRACT_90837)
    make_claim("HW-1", patient_name="Nguyen, Linh")
    post_era(client, era(paid("HW-1", "158.58")))

    report = get_report(client)

    assert report["tolerance_cents"] == 100
    assert report["claims"] == [
        {
            "claim_number": "HW-1",
            "patient_name": "Nguyen, Linh",
            "payer": "Aetna",
            "cpt_code": "90837",
            "date_of_service": "2026-09-21",
            "expected_cents": CONTRACT_90837,
            "allowed_cents": 15858,
            "variance_cents": 959,
        }
    ]
    assert report["total_variance_cents"] == 959


@pytest.mark.parametrize(
    ("allowed", "flagged"),
    [("168.17", False), ("167.42", False), ("167.17", False), ("167.16", True), ("170.00", False)],
)
def test_tolerance_is_one_dollar(client, make_claim, make_fee, allowed, flagged):
    make_fee("Aetna", "90837", CONTRACT_90837)
    make_claim("HW-1")
    post_era(client, era(paid("HW-1", allowed)))

    assert bool(get_report(client)["claims"]) is flagged


def test_patient_responsibility_counts_toward_allowed(client, make_claim, make_fee):
    """All of it went to the deductible: the payer allowed the full contract and paid $0."""
    make_fee("Aetna", "90837", CONTRACT_90837)
    make_claim("HW-1")
    post_era(client, era(line("HW-1", "200.00", "0.00", ("CO", "45", "31.83"), ("PR", "1", "168.17"))))

    assert get_report(client)["claims"] == []


def test_allowed_adds_up_across_remittances(client, make_claim, make_fee):
    """Underpaid first, then the payer sent the difference on a later remit."""
    make_fee("Aetna", "90837", CONTRACT_90837)
    make_claim("HW-1")
    post_era(client, era(paid("HW-1", "158.58"), trace="1000000001"))
    post_era(client, era(line("HW-1", "0.00", "9.59", ("CO", "45", "-9.59")), trace="1000000002"))

    assert get_report(client)["claims"] == []


def test_denied_unposted_and_uncontracted_claims_are_skipped(client, make_claim, make_fee):
    make_fee("Aetna", "90837", CONTRACT_90837)
    make_claim("HW-DENIED")
    make_claim("HW-UNPOSTED")
    make_claim("HW-NO-CONTRACT", cpt_code="90834")  # no Aetna 90834 contract on file
    post_era(
        client,
        era(
            line("HW-DENIED", "200.00", "0.00", ("CO", "197", "200.00"), status="4"),
            line("HW-NO-CONTRACT", "180.00", "50.00", ("CO", "45", "100.00"), ("PR", "3", "30.00")),
        ),
    )

    assert get_report(client) == {"tolerance_cents": 100, "total_variance_cents": 0, "claims": []}


def test_biggest_variance_first(client, make_claim, make_fee):
    make_fee("Aetna", "90837", CONTRACT_90837)
    make_fee("Cigna", "90837", 15875)
    make_claim("HW-1", payer="Aetna")
    make_claim("HW-2", payer="Aetna")
    make_claim("HW-3", payer="Cigna")
    post_era(client, era(paid("HW-1", "160.00"), paid("HW-2", "150.00"), payer="Aetna", trace="A1"))
    post_era(client, era(paid("HW-3", "150.00", copay="20.00"), payer="Cigna", trace="C1"))

    report = get_report(client)

    assert [(c["claim_number"], c["variance_cents"]) for c in report["claims"]] == [
        ("HW-2", 1817),
        ("HW-3", 875),
        ("HW-1", 817),
    ]
    assert report["total_variance_cents"] == 1817 + 875 + 817


def test_seeded_underpayments(client, db: Session):
    seed(db)

    report = get_report(client)

    assert [(c["claim_number"], c["variance_cents"]) for c in report["claims"]] == [
        ("HW-1050", 959),
        ("HW-1051", 959),
    ]
    assert report["total_variance_cents"] == 1918
