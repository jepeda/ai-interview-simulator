import pytest

from drills.ex11_context_managers import (
    ClinicError,
    EligibilityError,
    StagedChanges,
    audit,
    require_eligible,
)


def test_eligibility_error_is_a_clinic_error():
    err = EligibilityError(7, "plan terminated")
    assert isinstance(err, ClinicError)
    assert isinstance(err, Exception)


def test_eligibility_error_attributes_and_message():
    err = EligibilityError(patient_id=7, reason="plan terminated")
    assert err.patient_id == 7
    assert err.reason == "plan terminated"
    assert str(err) == "Patient 7 is not eligible: plan terminated"


def test_require_eligible_passes():
    assert require_eligible({"id": 1, "eligible": True, "reason": ""}) is None


def test_require_eligible_raises_catchable_as_base_class():
    with pytest.raises(ClinicError) as exc_info:
        require_eligible({"id": 3, "eligible": False, "reason": "no coverage"})
    assert exc_info.value.patient_id == 3


def test_audit_success():
    events: list[str] = []
    with audit(events, "bill"):
        events.append("work")
    assert events == ["start:bill", "work", "ok:bill"]


def test_audit_failure_records_error_and_reraises():
    events: list[str] = []
    with pytest.raises(RuntimeError):
        with audit(events, "bill"):
            raise RuntimeError("boom")
    assert events == ["start:bill", "error:bill"]


def test_staged_changes_applied_on_success():
    target = ["existing"]
    with StagedChanges(target) as staged:
        staged.append("a")
        staged.append("b")
        assert target == ["existing"]  # not applied until the block exits
    assert target == ["existing", "a", "b"]


def test_staged_changes_discarded_on_error_and_exception_propagates():
    target = ["existing"]
    with pytest.raises(ValueError):
        with StagedChanges(target) as staged:
            staged.append("a")
            raise ValueError("bad row")
    assert target == ["existing"]
