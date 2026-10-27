"""PART 2 (implement) -- provider search.

Ticket SRCH-112: "Find a therapist" search
  GET /providers/search?state=NY&payer=Aetna&specialty=anxiety&page=1&page_size=10

  * Only providers holding an UNEXPIRED license in `state` (ProviderLicense.expires_on >= today;
    the expiry date itself is still valid).
  * `payer` given -> provider must be in-network with that payer, compared case-insensitively
    ("aetna" matches "Aetna"). `payer` None -> self-pay search, no payer filter.
  * `specialty` given -> provider must have a Specialty with that slug.
  * accepting_new_patients_only (default True) -> hide providers not accepting new patients.
  * Each provider appears ONCE, however many licenses/payers/specialties match.
  * Order: rating high -> low, providers with no rating (None) LAST; ties by last_name, then first_name.
  * Pagination is 1-based. Return (providers on this page, total number of matches).

The router (routers/providers.py) already validates/normalizes the query string and calls this.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from booking.models import Provider


@dataclass(frozen=True)
class SearchCriteria:
    state: str  # two-letter, upper-case
    payer: str | None = None
    specialty: str | None = None
    accepting_new_patients_only: bool = True
    page: int = 1
    page_size: int = 10


def search_providers(db: Session, criteria: SearchCriteria, today: date) -> tuple[list[Provider], int]:
    # TODO(SRCH-112): implement. SQL (SQLAlchemy) or Python -- your call, but be ready to explain it.
    raise NotImplementedError("provider search is not implemented yet")
