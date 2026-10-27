"""Read-through cache for patient detail responses.

The patient detail endpoint is hot (every page view hits it), so serialized responses are
cached in-process. In production this would be Redis; the invalidation rules are the same.
"""

from sqlalchemy.orm import Session

from clinic.models import Patient
from clinic.schemas import PatientOut

_cache: dict[int, PatientOut] = {}


def get_patient_detail(db: Session, patient_id: int) -> PatientOut | None:
    cached = _cache.get(patient_id)
    if cached is not None:
        return cached

    patient = db.get(Patient, patient_id)
    if patient is None:
        return None

    detail = PatientOut.model_validate(patient)
    _cache[patient_id] = detail
    return detail


def invalidate(patient_id: int) -> None:
    """Drop one patient's cached detail. Call after any write to that patient."""
    _cache.pop(patient_id, None)


def clear() -> None:
    _cache.clear()
