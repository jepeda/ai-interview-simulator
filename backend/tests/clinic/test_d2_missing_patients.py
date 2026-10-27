import pytest


@pytest.fixture
def roster(make_plan, make_patient):
    aetna = make_plan(payer_name="Aetna")
    cigna = make_plan(payer_name="Cigna", plan_name="Open Access Plus")
    make_patient(first_name="Ada", last_name="King", insurance_plan=aetna, member_id="W1")
    make_patient(first_name="Dev", last_name="Patel")  # self-pay: no plan
    make_patient(first_name="Carmen", last_name="Diaz", insurance_plan=cigna, member_id="C1", status=None)  # legacy row
    make_patient(first_name="Hana", last_name="Sato", status=None)  # legacy + self-pay
    make_patient(first_name="Gus", last_name="Lindqvist", insurance_plan=aetna, member_id="W2", status="archived")


def names(response) -> list[str]:
    return [f"{p['first_name']} {p['last_name']}" for p in response.json()["items"]]


def test_lists_self_pay_and_legacy_patients(client, roster):
    response = client.get("/patients")
    assert response.status_code == 200
    assert names(response) == ["Carmen Diaz", "Ada King", "Dev Patel", "Hana Sato"]
    assert response.json()["total"] == 4


def test_archived_hidden_by_default_but_available(client, roster):
    assert "Gus Lindqvist" not in names(client.get("/patients"))
    with_archived = client.get("/patients", params={"include_archived": True})
    assert "Gus Lindqvist" in names(with_archived)
    assert with_archived.json()["total"] == 5


def test_payer_filter(client, roster):
    response = client.get("/patients", params={"payer": "Aetna"})
    assert names(response) == ["Ada King"]
    assert response.json()["total"] == 1


def test_pagination_uses_full_result_set(client, roster):
    page1 = client.get("/patients", params={"page": 1, "page_size": 3}).json()
    page2 = client.get("/patients", params={"page": 2, "page_size": 3}).json()
    assert page1["total"] == page2["total"] == 4
    assert len(page1["items"]) == 3
    assert [p["last_name"] for p in page2["items"]] == ["Sato"]


def test_patient_detail_for_self_pay_patient(client, make_patient):
    patient = make_patient(first_name="Dev", last_name="Patel")
    response = client.get(f"/patients/{patient.id}")
    assert response.status_code == 200
    assert response.json()["insurance_plan"] is None
