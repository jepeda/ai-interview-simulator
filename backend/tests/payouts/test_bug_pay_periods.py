"""Support ticket #5127: sessions land on the wrong pay statement (see the interview ticket).

Pay periods are the 1st-15th and 16th-end of month on the PROVIDER'S calendar.
"""

from datetime import date

from payouts_testkit import RATE_90834, RATE_90837, appointment_ids, statement
from sqlalchemy.orm import Session

from payouts.models import Provider
from payouts.seed import seed


def test_evening_session_belongs_to_local_pay_period(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    evening = make_appointment(maya, "2026-10-15 18:30")  # 01:30 UTC on Oct 16

    first_half = statement(client, maya, "2026-10-01")
    second_half = statement(client, maya, "2026-10-16")

    assert evening.id in appointment_ids(first_half)
    assert evening.id not in appointment_ids(second_half)
    assert first_half["total_cents"] == RATE_90837


def test_previous_evening_is_not_pulled_into_the_next_period(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    sep_30 = make_appointment(maya, "2026-09-30 17:30", cpt_code="90834")  # 00:30 UTC Oct 1

    assert sep_30.id not in appointment_ids(statement(client, maya, "2026-10-01"))
    september = statement(client, maya, "2026-09-16")
    assert appointment_ids(september) == [sep_30.id]
    assert september["total_cents"] == RATE_90834


def test_service_date_is_the_providers_calendar_date(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    make_appointment(maya, "2026-10-15 18:30")

    line = statement(client, maya, "2026-10-01")["lines"][0]
    assert line["service_date"] == "2026-10-15"
    assert line["starts_at"].startswith("2026-10-16T01:30")  # the instant itself is still UTC


def test_east_coast_provider_late_session_on_the_last_day(client, make_provider, make_appointment):
    jordan = make_provider("America/New_York")
    late = make_appointment(jordan, "2026-10-31 21:00")  # 01:00 UTC Nov 1
    early = make_appointment(jordan, "2026-11-01 00:30")  # 04:30 UTC Nov 1

    assert appointment_ids(statement(client, jordan, "2026-10-16")) == [late.id]
    assert appointment_ids(statement(client, jordan, "2026-11-01")) == [early.id]


def test_period_spanning_the_dst_change_keeps_its_local_days(client, make_provider, make_appointment):
    # Nov 1 2026: clocks go back (PDT -07:00 -> PST -08:00) inside the Nov 1-15 period.
    maya = make_provider("America/Los_Angeles")
    before = make_appointment(maya, "2026-10-31 23:30")  # PDT: 06:30 UTC Nov 1
    first = make_appointment(maya, "2026-11-01 00:15")  # PDT: 07:15 UTC Nov 1
    last = make_appointment(maya, "2026-11-15 23:30")  # PST: 07:30 UTC Nov 16
    after = make_appointment(maya, "2026-11-16 00:15")  # PST: 08:15 UTC Nov 16

    assert appointment_ids(statement(client, maya, "2026-10-16")) == [before.id]
    assert appointment_ids(statement(client, maya, "2026-11-01")) == [first.id, last.id]
    assert appointment_ids(statement(client, maya, "2026-11-16")) == [after.id]


def test_period_list_matches_statements(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    make_appointment(maya, "2026-10-14 09:00")
    make_appointment(maya, "2026-10-15 18:30")
    make_appointment(maya, "2026-10-20 10:00", cpt_code="90834")

    response = client.get(f"/providers/{maya.id}/periods")
    assert response.status_code == 200
    summary = {p["period_start"]: (p["session_count"], p["total_cents"]) for p in response.json()}
    assert summary == {
        "2026-10-16": (1, RATE_90834),
        "2026-10-01": (2, 2 * RATE_90837),
    }


def test_ticket_statement_matches_finance(client, db: Session):
    """The seeded data from the ticket: Dr. Patel's Oct 1-15 payout, per Finance."""
    seed(db)
    body = statement(client, db.get(Provider, 1), "2026-10-01")  # Dr. Maya Patel
    assert body["period_start"] == "2026-10-01"
    assert body["period_end"] == "2026-10-15"
    assert body["total_cents"] == 127050
    assert len(body["lines"]) == 8
    assert {line["service_date"] for line in body["lines"]} <= {
        f"2026-10-{d:02d}" for d in range(1, 16)
    }
    assert date.fromisoformat(body["lines"][-1]["service_date"]) == date(2026, 10, 15)
