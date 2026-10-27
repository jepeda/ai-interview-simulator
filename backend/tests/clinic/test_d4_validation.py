from datetime import date, timedelta

import pytest

VALID = {
    "first_name": "Ada",
    "last_name": "King",
    "date_of_birth": "1990-04-12",
    "email": "ada@example.com",
}


def error_fields(response) -> set[str]:
    """Collect the field names FastAPI reports in a 422 body: detail[].loc == ["body", "<field>"]."""
    return {str(err["loc"][-1]) for err in response.json()["detail"] if len(err["loc"]) > 1}


def test_create_self_pay_patient(client):
    response = client.post("/patients", json=VALID)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["date_of_birth"] == "1990-04-12"
    assert body["insurance_plan"] is None
    assert body["member_id"] is None
    assert body["status"] == "active"


def test_create_insured_patient(client, make_plan):
    plan = make_plan()
    response = client.post(
        "/patients", json=VALID | {"insurance_plan_id": plan.id, "member_id": "W123"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["insurance_plan"]["id"] == plan.id


def test_names_are_trimmed_and_email_lowercased(client):
    response = client.post(
        "/patients", json=VALID | {"first_name": "  Ada ", "email": " Ada@Example.COM "}
    )
    assert response.status_code == 201, response.text
    assert response.json()["first_name"] == "Ada"
    assert response.json()["email"] == "ada@example.com"


def test_blank_name_rejected(client):
    response = client.post("/patients", json=VALID | {"last_name": "   "})
    assert response.status_code == 422
    assert "last_name" in error_fields(response)


@pytest.mark.parametrize("bad_dob", ["04/12/1990", "not-a-date", "1990-13-01"])
def test_malformed_date_of_birth_is_422(client, bad_dob):
    response = client.post("/patients", json=VALID | {"date_of_birth": bad_dob})
    assert response.status_code == 422
    assert "date_of_birth" in error_fields(response)


def test_future_date_of_birth_rejected(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    response = client.post("/patients", json=VALID | {"date_of_birth": tomorrow})
    assert response.status_code == 422
    assert "date_of_birth" in error_fields(response)


@pytest.mark.parametrize("bad_email", ["ada", "ada@", "ada@example", "a da@example.com"])
def test_invalid_email_rejected(client, bad_email):
    response = client.post("/patients", json=VALID | {"email": bad_email})
    assert response.status_code == 422
    assert "email" in error_fields(response)


def test_plan_without_member_id_rejected(client, make_plan):
    plan = make_plan()
    response = client.post("/patients", json=VALID | {"insurance_plan_id": plan.id})
    assert response.status_code == 422
    assert "member_id" in response.text


def test_unknown_plan_rejected(client):
    response = client.post(
        "/patients", json=VALID | {"insurance_plan_id": 999, "member_id": "W123"}
    )
    assert response.status_code == 422
