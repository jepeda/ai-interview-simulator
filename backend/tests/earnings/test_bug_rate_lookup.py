"""Support ticket #6842: sessions after a rate increase are paid at the old rate (see the ticket).

Network Ops policy (README "Rates"): a session pays the entry in effect on its date of service, i.e.
the latest effective_date <= service_date. A correction is a new entry with the SAME effective date;
among entries with the same effective date, the one entered last wins. Entry order alone means
nothing else.
"""

from earnings_testkit import get_json, month, rate_card, rates_by_date, summary
from sqlalchemy.orm import Session

from earnings.models import Provider
from earnings.seed import seed


def ticket_rates(provider, make_rate) -> None:
    """Rosa's Aetna 60-minute rates: a typo, a mid-year increase, then a correction of the typo."""
    make_rate(provider, "Aetna", "90837", 14800, "2026-01-01", entered="2025-12-08 15:13", note="2026 contract")
    make_rate(provider, "Aetna", "90837", 17200, "2026-07-01", entered="2026-05-14 17:31", note="Increase")
    make_rate(provider, "Aetna", "90837", 15800, "2026-01-01", entered="2026-08-20 19:48", note="Correction")


def test_rate_increase_applies_from_its_effective_date(client, make_provider, make_rate, make_appointment):
    provider = make_provider()
    make_rate(provider, "Aetna", "90837", 15800, "2026-01-01")
    make_rate(provider, "Aetna", "90837", 17200, "2026-07-01")
    for day in ("2026-06-29", "2026-06-30", "2026-07-01", "2026-07-02"):
        make_appointment(provider, day)

    assert rates_by_date(month(client, provider, "2026-06")) == {"2026-06-29": 15800, "2026-06-30": 15800}
    assert rates_by_date(month(client, provider, "2026-07")) == {"2026-07-01": 17200, "2026-07-02": 17200}


def test_correction_entered_later_does_not_undo_a_later_increase(
    client, make_provider, make_rate, make_appointment
):
    provider = make_provider()
    ticket_rates(provider, make_rate)
    make_appointment(provider, "2026-07-01")
    make_appointment(provider, "2026-09-14")
    make_appointment(provider, "2026-10-19")

    assert rates_by_date(month(client, provider, "2026-07")) == {"2026-07-01": 17200}
    assert rates_by_date(month(client, provider, "2026-09")) == {"2026-09-14": 17200}
    assert rates_by_date(month(client, provider, "2026-10")) == {"2026-10-19": 17200}


def test_correction_replaces_the_original_entry_for_its_dates(client, make_provider, make_rate, make_appointment):
    provider = make_provider()
    ticket_rates(provider, make_rate)
    make_appointment(provider, "2026-01-05")
    make_appointment(provider, "2026-06-30")

    assert rates_by_date(month(client, provider, "2026-01")) == {"2026-01-05": 15800}
    assert rates_by_date(month(client, provider, "2026-06")) == {"2026-06-30": 15800}


def test_backdated_entry_does_not_override_a_newer_effective_date(
    client, make_provider, make_rate, make_appointment
):
    """Ops enters a rate effective in the past AFTER a later change was already scheduled."""
    provider = make_provider()
    make_rate(provider, "Optum", "90837", 15000, "2026-01-01", entered="2025-12-09 11:06")
    make_rate(provider, "Optum", "90837", 15500, "2026-09-01", entered="2026-08-03 14:02")
    make_rate(provider, "Optum", "90837", 15200, "2026-04-01", entered="2026-09-10 12:00")
    for day in ("2026-03-31", "2026-04-01", "2026-08-31", "2026-09-01", "2026-10-02"):
        make_appointment(provider, day, payer="Optum")

    rates = {}
    for key in ("2026-03", "2026-04", "2026-08", "2026-09", "2026-10"):
        rates |= rates_by_date(month(client, provider, key))
    assert rates == {
        "2026-03-31": 15000,
        "2026-04-01": 15200,
        "2026-08-31": 15200,
        "2026-09-01": 15500,
        "2026-10-02": 15500,
    }


def test_rate_scheduled_in_advance_waits_for_its_date(client, make_provider, make_rate, make_appointment):
    provider = make_provider()
    ticket_rates(provider, make_rate)
    make_rate(provider, "Aetna", "90837", 18000, "2027-01-01", entered="2026-10-02 16:20")
    make_appointment(provider, "2026-12-31")
    make_appointment(provider, "2027-01-01")

    assert rates_by_date(month(client, provider, "2026-12")) == {"2026-12-31": 17200}
    assert rates_by_date(month(client, provider, "2027-01")) == {"2027-01-01": 18000}


def test_other_payers_and_services_keep_their_own_rates(client, make_provider, make_rate, make_appointment):
    provider = make_provider()
    ticket_rates(provider, make_rate)
    make_rate(provider, "Aetna", "90834", 12500, "2026-01-01", entered="2025-12-08 15:12")
    make_rate(provider, "Aetna", "90834", 13600, "2026-07-01", entered="2026-05-14 17:30")
    make_rate(provider, "Cigna", "90837", 16000, "2026-01-01", entered="2025-12-09 10:42")
    make_appointment(provider, "2026-09-14", cpt_code="90837")
    make_appointment(provider, "2026-09-17", cpt_code="90834")
    make_appointment(provider, "2026-09-15", payer="Cigna")

    assert rates_by_date(month(client, provider, "2026-09")) == {
        "2026-09-14": 17200,
        "2026-09-15": 16000,
        "2026-09-17": 13600,
    }


def test_year_summary_uses_the_rate_in_effect(client, make_provider, make_rate, make_appointment):
    provider = make_provider()
    ticket_rates(provider, make_rate)
    make_rate(provider, "Cigna", "90837", 16000, "2026-01-01", entered="2025-12-09 10:42")
    make_appointment(provider, "2026-06-30")
    make_appointment(provider, "2026-07-01")
    make_appointment(provider, "2026-07-08")
    make_appointment(provider, "2026-07-09", payer="Cigna")

    body = summary(client, provider)

    assert body["total_cents"] == 15800 + 17200 * 2 + 16000
    assert body["months"] == [
        {"month": "2026-06", "session_count": 1, "earned_cents": 15800},
        {"month": "2026-07", "session_count": 3, "earned_cents": 17200 * 2 + 16000},
    ]
    assert body["by_payer"] == [
        {"payer": "Aetna", "session_count": 3, "earned_cents": 15800 + 17200 * 2},
        {"payer": "Cigna", "session_count": 1, "earned_cents": 16000},
    ]


def test_earnings_agree_with_the_rate_card(client, make_provider, make_rate, make_appointment):
    """The rate card (today = 2026-10-23) and the earnings pages must never disagree."""
    provider = make_provider()
    ticket_rates(provider, make_rate)
    make_appointment(provider, "2026-10-23")

    card = rate_card(client, provider)[("Aetna", "90837")]

    assert card["current"] == {"rate_cents": 17200, "effective_date": "2026-07-01"}
    assert rates_by_date(month(client, provider, "2026-10")) == {"2026-10-23": card["current"]["rate_cents"]}


def test_rate_history_stays_in_the_order_ops_entered_it(client, make_provider, make_rate):
    """The audit trail (GET /rates) is used by Network Ops and Finance: keep it in entry order."""
    provider = make_provider()
    ticket_rates(provider, make_rate)

    history = get_json(client, f"/providers/{provider.id}/rates")

    assert [(e["effective_date"], e["rate_cents"]) for e in history] == [
        ("2026-01-01", 14800),
        ("2026-07-01", 17200),
        ("2026-01-01", 15800),
    ]


def test_ticket_numbers_match_finance(client, db: Session):
    """The seeded data from the ticket: Rosa Delgado's 2026 earnings, per Finance."""
    seed(db)
    rosa = db.get(Provider, 1)

    body = summary(client, rosa)
    assert body["total_cents"] == 2013500
    assert body["session_count"] == 132
    months = {m["month"]: m["earned_cents"] for m in body["months"]}
    assert months["2026-07"] == 204800
    assert months["2026-09"] == 227800
    assert months["2026-10"] == 196200
    assert "2026-08" not in months  # on leave all of August
    assert body["by_payer"][0] == {"payer": "Aetna", "session_count": 85, "earned_cents": 1286200}
