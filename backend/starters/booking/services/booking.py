"""PARTS 3 & 4 (implement) -- booking and cancelling appointments."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from booking.models import Appointment
from booking.schemas import BookingRequest, CancelRequest

LATE_CANCEL_WINDOW = timedelta(hours=24)


def book_appointment(db: Session, request: BookingRequest, now: datetime) -> tuple[Appointment, bool]:
    """PART 3. Ticket BOOK-207: book a session. Returns (appointment, created).

    1. Idempotency (clients retry on flaky networks). If request.idempotency_key is set and an
       appointment with that key exists:
         - same provider_id, patient_id and starts_at  -> return (existing, False)   [router sends 200]
         - anything different                           -> IdempotencyKeyReused
       Do this BEFORE the other checks: a retry must succeed even though its slot is now taken (by itself).
    2. Unknown provider or patient -> NotFound (see repositories/providers.py).
    3. The provider must hold an unexpired license (expires_on >= now's date) for the PATIENT's
       state -> otherwise NotLicensedInState.
    4. If the patient has a payer, the provider must accept it (case-insensitive) -> PayerNotAccepted.
       Self-pay patients (payer None) can book anyone.
    5. starts_at must be exactly one of the provider's open slots (reuse services/availability.py;
       repositories/appointments.py has the query you need) -> otherwise SlotUnavailable.
    6. Save: ends_at = starts_at + provider.session_minutes, status "booked", created_at = now,
       idempotency_key stored. All datetimes stored as naive UTC (timeutil.to_db).  -> (appointment, True)
    """
    # TODO(BOOK-207)
    raise NotImplementedError("booking is not implemented yet")


def cancel_appointment(
    db: Session, appointment_id: int, request: CancelRequest, now: datetime
) -> Appointment:
    """PART 4. Ticket BOOK-219: cancel a session.

    * Unknown appointment -> NotFound.
    * Only "booked" appointments can be cancelled; anything else -> InvalidTransition.
    * An appointment that has already started (starts_at <= now) -> InvalidTransition.
    * Late-cancel fee: if the PATIENT cancels less than LATE_CANCEL_WINDOW before the start, charge
      50% of the provider's session_rate_cents, rounding half a cent UP (15001 -> 7501).
      Exactly 24h before is NOT late. Provider cancellations never incur a fee.
    * Set status "cancelled", cancelled_at = now (naive UTC), cancelled_by, cancel_reason (request.reason),
      late_cancel_fee_cents. The slot must become bookable again (that's Part 1's job).
    """
    # TODO(BOOK-219)
    raise NotImplementedError("cancellation is not implemented yet")
