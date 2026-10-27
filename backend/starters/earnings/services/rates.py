"""What a session pays: the provider's contracted rate in effect on its date of service.

The earnings pages price a whole year of sessions at once, so instead of one query per session we
load the provider's fee schedule once and look rates up in memory.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from sqlalchemy.orm import Session

from earnings.errors import MissingRate
from earnings.models import Appointment, ContractedRate
from earnings.repositories import rates as rates_repo


class RateTable:
    def __init__(self, entries: Iterable[ContractedRate]) -> None:
        self._entries: dict[tuple[str, str], list[ContractedRate]] = defaultdict(list)
        for entry in entries:
            self._entries[(entry.payer, entry.cpt_code)].append(entry)

    def entry_on(self, payer: str, cpt_code: str, day: date) -> ContractedRate | None:
        """The fee-schedule entry that applies to a session on `day` (None: no contract yet)."""
        applicable = [e for e in self._entries.get((payer, cpt_code), []) if e.effective_date <= day]
        return applicable[-1] if applicable else None

    def rate_for(self, appointment: Appointment) -> int:
        entry = self.entry_on(appointment.payer, appointment.cpt_code, appointment.service_date)
        if entry is None:
            raise MissingRate(
                f"No contracted rate for {appointment.payer} {appointment.cpt_code} on "
                f"{appointment.service_date.isoformat()} (appointment {appointment.id})"
            )
        return entry.rate_cents


def load_rate_table(db: Session, provider_id: int) -> RateTable:
    return RateTable(rates_repo.list_for_provider(db, provider_id))
