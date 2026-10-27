"""Feature: Network Ops schedules (and cancels) future rate changes through the API.

Tests run with today = 2026-10-23 (see earnings_testkit.TODAY).
"""

import pytest
from earnings_testkit import get_json, rate_card


def schedule(client, provider, **overrides):
    body = {"payer": "Aetna", "cpt_code": "90837", "rate_cents": 18000, "effective_date": "2027-01-01"}
    body.update(overrides)
    return client.post(f"/providers/{provider.id}/rates", json=body)


@pytest.fixture
def provider(make_provider, make_rate):
    p = make_provider()
    make_rate(p, "Aetna", "90837", 15800, "2026-01-01")
    make_rate(p, "Aetna", "90837", 17200, "2026-07-01")
    make_rate(p, "Aetna", "90834", 13600, "2026-07-01")
    return p


def test_schedule_a_rate_increase(client, provider):
    response = schedule(client, provider, note="2027 increase")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] > 0
    assert (body["payer"], body["cpt_code"], body["rate_cents"]) == ("Aetna", "90837", 18000)
    assert (body["effective_date"], body["note"]) == ("2027-01-01", "2027 increase")
    history = get_json(client, f"/providers/{provider.id}/rates")
    assert history[-1]["id"] == body["id"]


def test_rate_card_shows_the_scheduled_change(client, provider):
    assert schedule(client, provider).status_code == 201

    row = rate_card(client, provider)[("Aetna", "90837")]

    assert row["current"] == {"rate_cents": 17200, "effective_date": "2026-07-01"}
    assert row["upcoming"] == {"rate_cents": 18000, "effective_date": "2027-01-01"}


def test_new_payer_contract_can_start_in_the_future(client, provider):
    response = schedule(client, provider, payer="Cigna", cpt_code="90834", rate_cents=13000)

    assert response.status_code == 201, response.text
    row = rate_card(client, provider)[("Cigna", "90834")]
    assert row["current"] is None
    assert row["upcoming"] == {"rate_cents": 13000, "effective_date": "2027-01-01"}


@pytest.mark.parametrize("effective_date", ["2026-10-23", "2026-07-01", "2025-12-31"])
def test_changes_must_take_effect_after_today(client, provider, effective_date):
    response = schedule(client, provider, effective_date=effective_date)

    assert response.status_code == 422
    assert len(get_json(client, f"/providers/{provider.id}/rates")) == 3


@pytest.mark.parametrize(
    "overrides",
    [{"rate_cents": 0}, {"rate_cents": -500}, {"cpt_code": "99213"}, {"payer": "Blue Shield"}],
)
def test_invalid_rate_changes_are_rejected(client, provider, overrides):
    assert schedule(client, provider, **overrides).status_code == 422


def test_only_one_pending_change_per_payer_and_service(client, provider):
    assert schedule(client, provider, effective_date="2027-01-01").status_code == 201

    same_day = schedule(client, provider, effective_date="2027-01-01", rate_cents=18500)
    other_day = schedule(client, provider, effective_date="2027-03-01", rate_cents=18500)

    for response in (same_day, other_day):
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "rate_change_conflict"
    # Other services and payers are independent.
    assert schedule(client, provider, cpt_code="90834", rate_cents=14200).status_code == 201


def test_cancel_a_scheduled_change(client, provider):
    rate_id = schedule(client, provider).json()["id"]

    response = client.delete(f"/providers/{provider.id}/rates/{rate_id}")

    assert response.status_code == 204
    assert rate_card(client, provider)[("Aetna", "90837")]["upcoming"] is None
    # ...and now a different change can be scheduled.
    assert schedule(client, provider, effective_date="2027-02-01").status_code == 201


def test_rates_in_effect_cannot_be_cancelled(client, provider):
    history = get_json(client, f"/providers/{provider.id}/rates")
    in_effect = history[1]["id"]  # Aetna 90837 since 2026-07-01

    response = client.delete(f"/providers/{provider.id}/rates/{in_effect}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "rate_in_effect"
    assert len(get_json(client, f"/providers/{provider.id}/rates")) == 3


def test_unknown_provider_or_rate(client, provider, make_provider):
    other = make_provider()
    rate_id = schedule(client, provider).json()["id"]

    body = {"payer": "Aetna", "cpt_code": "90837", "rate_cents": 18000, "effective_date": "2027-01-01"}
    assert client.post("/providers/9999/rates", json=body).status_code == 404
    assert client.delete(f"/providers/{provider.id}/rates/9999").status_code == 404
    assert client.delete(f"/providers/{other.id}/rates/{rate_id}").status_code == 404
