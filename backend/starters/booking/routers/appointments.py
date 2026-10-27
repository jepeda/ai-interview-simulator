from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from booking.clock import Now
from booking.db import get_db
from booking.repositories import appointments as appointments_repo
from booking.schemas import AppointmentOut, BookingRequest, CancelRequest
from booking.services import booking

router = APIRouter(prefix="/appointments", tags=["appointments"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(payload: BookingRequest, response: Response, db: DbSession, now: Now) -> AppointmentOut:
    appointment, created = booking.book_appointment(db, payload, now)
    if not created:
        response.status_code = 200  # idempotent replay
    return AppointmentOut.from_model(appointment)


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: DbSession) -> AppointmentOut:
    return AppointmentOut.from_model(appointments_repo.get_appointment(db, appointment_id))


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(appointment_id: int, payload: CancelRequest, db: DbSession, now: Now) -> AppointmentOut:
    return AppointmentOut.from_model(booking.cancel_appointment(db, appointment_id, payload, now))
