"""Backend half of the stale-data bug. The frontend half is tested by
frontend/tests/patientState.test.ts (the dashboard runs both)."""

import pytest


@pytest.fixture
def setup(make_plan, make_patient):
    aetna = make_plan(payer_name="Aetna")
    cigna = make_plan(payer_name="Cigna", plan_name="Open Access Plus")
    patient = make_patient(insurance_plan=aetna, member_id="W1")
    return patient, aetna, cigna


def test_patch_response_reflects_update(client, setup):
    patient, _, cigna = setup
    client.get(f"/patients/{patient.id}")  # the front desk opened the chart (warms the cache)

    response = client.patch(
        f"/patients/{patient.id}/coverage",
        json={"insurance_plan_id": cigna.id, "member_id": "C-777"},
    )

    assert response.status_code == 200
    assert response.json()["insurance_plan"]["payer_name"] == "Cigna"
    assert response.json()["member_id"] == "C-777"


def test_get_after_patch_is_fresh(client, setup):
    patient, _, cigna = setup
    client.get(f"/patients/{patient.id}")
    client.patch(
        f"/patients/{patient.id}/coverage",
        json={"insurance_plan_id": cigna.id, "member_id": "C-777"},
    )

    detail = client.get(f"/patients/{patient.id}").json()

    assert detail["insurance_plan"]["payer_name"] == "Cigna"
    assert detail["member_id"] == "C-777"


def test_removing_coverage(client, setup):
    patient, _, _ = setup
    client.get(f"/patients/{patient.id}")

    client.patch(f"/patients/{patient.id}/coverage", json={"insurance_plan_id": None})

    detail = client.get(f"/patients/{patient.id}").json()
    assert detail["insurance_plan"] is None
    assert detail["member_id"] is None


def test_detail_and_list_agree_after_update(client, setup):
    patient, _, cigna = setup
    client.get(f"/patients/{patient.id}")
    client.patch(
        f"/patients/{patient.id}/coverage",
        json={"insurance_plan_id": cigna.id, "member_id": "C-777"},
    )

    detail = client.get(f"/patients/{patient.id}").json()
    listed = next(p for p in client.get("/patients").json()["items"] if p["id"] == patient.id)
    assert detail == listed
