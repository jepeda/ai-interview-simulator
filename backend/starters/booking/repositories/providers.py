from sqlalchemy.orm import Session

from booking.errors import NotFound
from booking.models import Patient, Provider


def get_provider(db: Session, provider_id: int) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise NotFound(f"Provider {provider_id} not found")
    return provider


def get_patient(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise NotFound(f"Patient {patient_id} not found")
    return patient
