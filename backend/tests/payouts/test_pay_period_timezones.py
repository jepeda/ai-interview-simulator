"""Regression tests for ticket #5127: pay periods are the provider's local days, not UTC days.

Covers the cases test_bug_pay_periods.py doesn't: the conversion helpers themselves, timezones
east of UTC, exact local-midnight boundaries, and winter (PST) offsets.
"""

from datetime import date, datetime

from payouts_testkit import RATE_90834, RATE_90837, appointment_ids, statement

from payouts.services.periods import PayPeriod, query_bounds
from payouts.timeutil import local_date, zone

LA = zone("America/Los_Angeles")


def test_local_date_uses_the_providers_calendar():
    stored = datetime(2026, 10, 16, 1, 30)  # naive UTC, as in the DB
    assert local_date(stored, LA) == date(2026, 10, 15)
    assert local_date(stored, zone("Asia/Tokyo")) == date(2026, 10, 16)
    assert local_date(stored, zone("UTC")) == date(2026, 10, 16)


def test_query_bounds_are_local_midnights_in_utc():
    summer = query_bounds(PayPeriod(date(2026, 10, 1), date(2026, 10, 15)), LA)
    assert summer == (datetime(2026, 10, 1, 7, 0), datetime(2026, 10, 16, 7, 0))  # PDT -07:00

    winter = query_bounds(PayPeriod(date(2026, 12, 1), date(2026, 12, 15)), LA)
    assert winter == (datetime(2026, 12, 1, 8, 0), datetime(2026, 12, 16, 8, 0))  # PST -08:00


def test_query_bounds_across_the_dst_change():
    # Nov 1 2026 starts on PDT (-07:00); by Nov 16 the clocks have gone back to PST (-08:00).
    bounds = query_bounds(PayPeriod(date(2026, 11, 1), date(2026, 11, 15)), LA)
    assert bounds == (datetime(2026, 11, 1, 7, 0), datetime(2026, 11, 16, 8, 0))


def test_query_bounds_across_the_new_year():
    december = query_bounds(PayPeriod(date(2026, 12, 16), date(2026, 12, 31)), LA)
    january = query_bounds(PayPeriod(date(2027, 1, 1), date(2027, 1, 15)), LA)
    assert december == (datetime(2026, 12, 16, 8, 0), datetime(2027, 1, 1, 8, 0))
    assert january == (datetime(2027, 1, 1, 8, 0), datetime(2027, 1, 16, 8, 0))
    assert december[1] == january[0]  # no gap or overlap at midnight on New Year's


def test_new_years_eve_session_stays_in_december(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    nye = make_appointment(maya, "2026-12-31 19:00")  # PST: 03:00 UTC Jan 1 2027
    new_year = make_appointment(maya, "2027-01-01 00:30")  # PST: 08:30 UTC Jan 1 2027

    december = statement(client, maya, "2026-12-16")
    january = statement(client, maya, "2027-01-01")

    assert appointment_ids(december) == [nye.id]
    assert december["lines"][0]["service_date"] == "2026-12-31"
    assert appointment_ids(january) == [new_year.id]
    assert (january["period_start"], january["period_end"]) == ("2027-01-01", "2027-01-15")
    assert january["lines"][0]["service_date"] == "2027-01-01"


def test_east_of_utc_morning_session_stays_in_its_local_period(client, make_provider, make_appointment):
    kenji = make_provider("Asia/Tokyo")
    morning = make_appointment(kenji, "2026-10-16 08:00")  # 23:00 UTC Oct 15

    assert appointment_ids(statement(client, kenji, "2026-10-16")) == [morning.id]
    assert appointment_ids(statement(client, kenji, "2026-10-01")) == []


def test_local_midnight_starts_the_next_period(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    last_minute = make_appointment(maya, "2026-10-15 23:59")
    midnight = make_appointment(maya, "2026-10-16 00:00")

    assert appointment_ids(statement(client, maya, "2026-10-01")) == [last_minute.id]
    assert appointment_ids(statement(client, maya, "2026-10-16")) == [midnight.id]


def test_winter_evening_session_on_the_15th(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    evening = make_appointment(maya, "2026-12-15 16:30")  # PST: 00:30 UTC Dec 16

    first_half = statement(client, maya, "2026-12-01")
    assert appointment_ids(first_half) == [evening.id]
    assert first_half["lines"][0]["service_date"] == "2026-12-15"
    assert appointment_ids(statement(client, maya, "2026-12-16")) == []


def test_period_list_puts_boundary_sessions_in_their_local_periods(client, make_provider, make_appointment):
    maya = make_provider("America/Los_Angeles")
    make_appointment(maya, "2026-09-30 17:30", cpt_code="90834")  # 00:30 UTC Oct 1
    make_appointment(maya, "2026-10-15 18:30")  # 01:30 UTC Oct 16

    response = client.get(f"/providers/{maya.id}/periods")
    assert response.status_code == 200
    summary = {p["period_start"]: (p["session_count"], p["total_cents"]) for p in response.json()}
    assert summary == {
        "2026-10-01": (1, RATE_90837),
        "2026-09-16": (1, RATE_90834),
    }
