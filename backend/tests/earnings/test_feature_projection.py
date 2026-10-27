"""Feature: projected earnings for a month (earned so far + booked sessions still to come)."""

from datetime import date

from earnings_testkit import get_json
from sqlalchemy.orm import Session

from earnings.models import Provider, SessionStatus
from earnings.seed import seed

S = SessionStatus


def projection(client, provider, month_key: str) -> dict:
    return get_json(client, f"/providers/{provider.id}/projection/{month_key}")


def contracted(make_provider, make_rate):
    provider = make_provider()
    make_rate(provider, "Aetna", "90837", 17200, "2026-07-01")
    make_rate(provider, "Aetna", "90834", 13600, "2026-07-01")
    return provider


def test_earned_plus_booked(client, make_provider, make_rate, make_appointment, set_today):
    set_today(date(2026, 10, 14))
    provider = contracted(make_provider, make_rate)
    make_appointment(provider, "2026-10-05")
    make_appointment(provider, "2026-10-12", cpt_code="90834")
    make_appointment(provider, "2026-10-14", status=S.SCHEDULED)  # later today: still to come
    make_appointment(provider, "2026-10-19", status=S.SCHEDULED)
    make_appointment(provider, "2026-10-26", status=S.SCHEDULED, cpt_code="90834")
    make_appointment(provider, "2026-11-02", status=S.SCHEDULED)  # next month

    body = projection(client, provider, "2026-10")

    assert body["provider_id"] == provider.id
    assert body["month"] == "2026-10"
    assert (body["completed_count"], body["earned_cents"]) == (2, 17200 + 13600)
    assert (body["scheduled_count"], body["projected_cents"]) == (3, 2 * 17200 + 13600)
    assert body["total_cents"] == body["earned_cents"] + body["projected_cents"]
    assert body["undocumented_count"] == 0


def test_booked_sessions_use_the_rate_on_their_own_date(
    client, make_provider, make_rate, make_appointment, set_today
):
    set_today(date(2026, 12, 7))
    provider = contracted(make_provider, make_rate)
    make_rate(provider, "Aetna", "90837", 18000, "2026-12-15")  # scheduled mid-month increase
    make_appointment(provider, "2026-12-14", status=S.SCHEDULED)
    make_appointment(provider, "2026-12-15", status=S.SCHEDULED)
    make_appointment(provider, "2026-12-21", status=S.SCHEDULED)

    assert projection(client, provider, "2026-12")["projected_cents"] == 17200 + 2 * 18000


def test_unbillable_and_undocumented_sessions_are_not_projected(
    client, make_provider, make_rate, make_appointment, set_today
):
    set_today(date(2026, 10, 14))
    provider = contracted(make_provider, make_rate)
    make_appointment(provider, "2026-10-06", status=S.SCHEDULED)  # never documented
    make_appointment(provider, "2026-10-07", status=S.NO_SHOW)
    make_appointment(provider, "2026-10-08", status=S.CANCELLED)
    make_appointment(provider, "2026-10-20", status=S.CANCELLED)
    make_appointment(provider, "2026-10-21", status=S.SCHEDULED)

    body = projection(client, provider, "2026-10")

    assert body["earned_cents"] == 0
    assert (body["scheduled_count"], body["projected_cents"]) == (1, 17200)
    assert body["undocumented_count"] == 1
    assert body["total_cents"] == 17200


def test_past_month_has_nothing_left_to_project(client, make_provider, make_rate, make_appointment, set_today):
    set_today(date(2026, 10, 14))
    provider = contracted(make_provider, make_rate)
    make_appointment(provider, "2026-09-14")
    make_appointment(provider, "2026-09-21", status=S.SCHEDULED)

    body = projection(client, provider, "2026-09")

    assert (body["earned_cents"], body["projected_cents"], body["total_cents"]) == (17200, 0, 17200)
    assert (body["scheduled_count"], body["undocumented_count"]) == (0, 1)


def test_bad_month_or_provider(client, make_provider, make_rate):
    provider = contracted(make_provider, make_rate)

    assert client.get(f"/providers/{provider.id}/projection/2026-13").status_code == 422
    assert client.get(f"/providers/{provider.id}/projection/october").status_code == 422
    assert client.get("/providers/9999/projection/2026-10").status_code == 404


def test_seeded_provider_this_month(client, db: Session):
    """Rosa Delgado on Fri Oct 23 2026 (the tests' today)."""
    seed(db)
    body = projection(client, db.get(Provider, 1), "2026-10")

    assert (body["completed_count"], body["earned_cents"]) == (13, 196200)
    # Oct 26 Aetna 90837 + Oct 27 Cigna 90834 + Oct 29 Aetna 90834 + Oct 30 Optum 90837
    assert (body["scheduled_count"], body["projected_cents"]) == (4, 17200 + 12800 + 13600 + 15500)
    assert body["total_cents"] == 196200 + 59100
