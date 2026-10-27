"""Feature: show the expected pay date (5 business days after the period ends)."""

import pytest


@pytest.mark.parametrize(
    ("period_start", "pay_date"),
    [
        ("2026-10-01", "2026-10-22"),  # ends Thu Oct 15
        ("2026-10-16", "2026-11-06"),  # ends Sat Oct 31: the weekend doesn't count
        ("2026-11-01", "2026-11-20"),  # ends Sun Nov 15
        ("2026-11-16", "2026-12-07"),  # ends Mon Nov 30
        ("2026-12-16", "2027-01-08"),  # ends Thu Dec 31: Jan 1 is a Acme Health holiday
    ],
)
def test_statement_pay_date(client, make_provider, make_appointment, period_start, pay_date):
    provider = make_provider()
    make_appointment(provider, f"{period_start} 10:00")

    response = client.get(f"/providers/{provider.id}/statements/{period_start}")

    assert response.status_code == 200, response.text
    assert response.json()["pay_date"] == pay_date


def test_period_list_includes_pay_dates(client, make_provider, make_appointment):
    provider = make_provider()
    make_appointment(provider, "2026-10-06 10:00")
    make_appointment(provider, "2026-10-20 10:00")

    response = client.get(f"/providers/{provider.id}/periods")

    assert response.status_code == 200
    assert {p["period_start"]: p["pay_date"] for p in response.json()} == {
        "2026-10-16": "2026-11-06",
        "2026-10-01": "2026-10-22",
    }
