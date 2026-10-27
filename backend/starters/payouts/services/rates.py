"""What Acme Health owes a provider for one appointment."""

from dataclasses import dataclass

from payouts.errors import MissingFeeSchedule
from payouts.models import Appointment, Provider, SessionStatus


@dataclass(frozen=True)
class Payable:
    kind: str  # "session" | "late_cancel"
    amount_cents: int


def payable_for(
    appointment: Appointment, provider: Provider, fees: dict[tuple[str, str], int]
) -> Payable | None:
    """None when the appointment pays nothing (no-show, cancelled in time)."""
    match appointment.status:
        case SessionStatus.COMPLETED:
            rate = fees.get((appointment.payer, appointment.cpt_code))
            if rate is None:
                raise MissingFeeSchedule(
                    f"No contracted rate for {appointment.payer} {appointment.cpt_code} "
                    f"(provider {provider.id}, appointment {appointment.id})"
                )
            return Payable("session", rate)
        case SessionStatus.LATE_CANCEL:
            return Payable("late_cancel", provider.late_cancel_fee_cents)
        case _:
            return None
