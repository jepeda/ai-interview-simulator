from datetime import date

import pytest

from clinic.models import InsurancePlan
from clinic.services.eligibility import EligibilityStatus, check_eligibility

TODAY = date(2026, 10, 26)


def plan(effective: date = date(2024, 1, 1), terminates: date | None = None) -> InsurancePlan:
    return InsurancePlan(
        payer_name="Aetna",
        plan_name="Choice POS II",
        copay_cents=2500,
        effective_date=effective,
        termination_date=terminates,
    )


def test_open_ended_plan_is_eligible():
    result = check_eligibility(plan(terminates=None), "W123", TODAY)
    assert result.status == EligibilityStatus.ELIGIBLE


def test_termination_date_is_last_covered_day():
    result = check_eligibility(plan(terminates=TODAY), "W123", TODAY)
    assert result.status == EligibilityStatus.ELIGIBLE


def test_day_after_termination_is_terminated():
    result = check_eligibility(plan(terminates=date(2026, 10, 25)), "W123", TODAY)
    assert result.status == EligibilityStatus.TERMINATED


def test_before_effective_date_is_not_yet_active():
    result = check_eligibility(plan(effective=date(2026, 11, 1)), "W123", TODAY)
    assert result.status == EligibilityStatus.NOT_YET_ACTIVE


def test_effective_date_itself_is_covered():
    result = check_eligibility(plan(effective=TODAY), "W123", TODAY)
    assert result.status == EligibilityStatus.ELIGIBLE


def test_no_plan_is_no_coverage():
    assert check_eligibility(None, None, TODAY).status == EligibilityStatus.NO_COVERAGE


@pytest.mark.parametrize("member_id", [None, ""])
def test_plan_without_member_id_is_no_coverage(member_id):
    result = check_eligibility(plan(), member_id, TODAY)
    assert result.status == EligibilityStatus.NO_COVERAGE


def test_eligibility_endpoint(client, make_plan, make_patient):
    aetna = make_plan(termination_date=None)
    patient = make_patient(insurance_plan=aetna, member_id="W123")

    response = client.get(f"/patients/{patient.id}/eligibility", params={"on": "2026-10-26"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "eligible"
    assert body["checked_on"] == "2026-10-26"
    assert body["plan"]["payer_name"] == "Aetna"


def test_eligibility_endpoint_unknown_patient(client):
    assert client.get("/patients/999/eligibility").status_code == 404
