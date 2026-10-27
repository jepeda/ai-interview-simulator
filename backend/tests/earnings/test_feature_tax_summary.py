"""Feature: annual 1099-NEC summary (what Acme Health PAID the provider in a calendar year)."""

from earnings_testkit import get_json
from sqlalchemy.orm import Session

from earnings.models import Provider, SessionStatus
from earnings.seed import seed


def tax(client, provider, year: int) -> dict:
    return get_json(client, f"/providers/{provider.id}/tax-summary/{year}")


def contracted(make_provider, make_rate):
    provider = make_provider()
    make_rate(provider, "Aetna", "90837", 15000, "2025-01-01")
    make_rate(provider, "Aetna", "90837", 15800, "2026-01-01")
    make_rate(provider, "Cigna", "90837", 16000, "2025-01-01")
    make_rate(provider, "Cigna", "90834", 12800, "2025-01-01")
    return provider


def test_paid_sessions_by_payer(client, make_provider, make_rate, make_appointment):
    provider = contracted(make_provider, make_rate)
    make_appointment(provider, "2026-03-02", paid_on="2026-03-13")
    make_appointment(provider, "2026-03-09", paid_on="2026-03-20")
    make_appointment(provider, "2026-03-03", payer="Cigna", paid_on="2026-03-13")
    make_appointment(provider, "2026-03-10", payer="Cigna", cpt_code="90834", paid_on="2026-03-20")

    body = tax(client, provider, 2026)

    assert body["provider_id"] == provider.id
    assert body["year"] == 2026
    assert body["by_payer"] == [
        {"payer": "Aetna", "session_count": 2, "amount_cents": 2 * 15800},
        {"payer": "Cigna", "session_count": 2, "amount_cents": 16000 + 12800},
    ]
    assert body["sessions_cents"] == body["total_cents"] == 2 * 15800 + 16000 + 12800
    assert body["adjustments_cents"] == 0
    assert body["form_1099_required"] is True  # $604.00 >= $600


def test_counts_by_pay_date_at_the_rate_on_the_date_of_service(
    client, make_provider, make_rate, make_appointment
):
    provider = contracted(make_provider, make_rate)
    make_appointment(provider, "2025-12-29", paid_on="2026-01-09")
    make_appointment(provider, "2025-12-15", paid_on="2025-12-26")
    make_appointment(provider, "2026-12-28")  # not paid yet: belongs to whichever year it's paid in

    assert tax(client, provider, 2026)["sessions_cents"] == 15000  # 2025 rate, paid in 2026
    assert tax(client, provider, 2025)["sessions_cents"] == 15000


def test_unpaid_and_unbillable_sessions_are_excluded(client, make_provider, make_rate, make_appointment):
    provider = contracted(make_provider, make_rate)
    make_appointment(provider, "2026-05-04", paid_on="2026-05-15")
    make_appointment(provider, "2026-10-19")  # completed, payout pending
    make_appointment(provider, "2026-05-05", status=SessionStatus.NO_SHOW)
    make_appointment(provider, "2026-05-06", status=SessionStatus.CANCELLED)
    make_appointment(provider, "2026-11-02", status=SessionStatus.SCHEDULED)

    body = tax(client, provider, 2026)

    assert body["by_payer"] == [{"payer": "Aetna", "session_count": 1, "amount_cents": 15800}]


def test_adjustments_count_in_their_effective_year(
    client, make_provider, make_rate, make_appointment, make_adjustment
):
    provider = contracted(make_provider, make_rate)
    for day in ("2026-02-02", "2026-02-09", "2026-02-16", "2026-02-23"):
        make_appointment(provider, day, paid_on="2026-03-06")
    make_adjustment(provider, "2026-03-20", 25000, "Telehealth stipend")
    make_adjustment(provider, "2026-09-18", -15800, "Recoupment: duplicate claim")
    make_adjustment(provider, "2025-12-31", 10000, "Stipend (last year)")

    body = tax(client, provider, 2026)

    assert body["sessions_cents"] == 4 * 15800
    assert body["adjustments_cents"] == 25000 - 15800
    assert body["total_cents"] == 4 * 15800 + 25000 - 15800
    assert body["form_1099_required"] is True


def test_form_1099_threshold_is_600_dollars(client, make_provider, make_rate, make_appointment, make_adjustment):
    provider = contracted(make_provider, make_rate)
    for day in ("2026-02-02", "2026-02-09", "2026-02-16"):
        make_appointment(provider, day, paid_on="2026-03-06")  # 3 x 158.00 = 474.00
    make_adjustment(provider, "2026-04-01", 12600, "Stipend")  # -> exactly 600.00

    assert tax(client, provider, 2026)["total_cents"] == 60000
    assert tax(client, provider, 2026)["form_1099_required"] is True

    make_adjustment(provider, "2026-04-02", -1, "Rounding")
    assert tax(client, provider, 2026)["form_1099_required"] is False


def test_year_without_payments(client, make_provider, make_rate):
    provider = contracted(make_provider, make_rate)

    assert tax(client, provider, 2024) == {
        "provider_id": provider.id,
        "year": 2024,
        "sessions_cents": 0,
        "adjustments_cents": 0,
        "total_cents": 0,
        "by_payer": [],
        "form_1099_required": False,
    }
    assert client.get("/providers/9999/tax-summary/2026").status_code == 404


def test_seeded_provider(client, db: Session):
    seed(db)
    body = tax(client, db.get(Provider, 1), 2026)  # Rosa Delgado

    assert body["adjustments_cents"] == 25000 + 34000 - 17200
    assert body["total_cents"] == body["sessions_cents"] + body["adjustments_cents"]
    assert [p["payer"] for p in body["by_payer"]] == ["Aetna", "Cigna", "Optum"]
