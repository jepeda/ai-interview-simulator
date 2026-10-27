"""PART 2 -- provider search (reference solution).

`.any()` on a relationship compiles to EXISTS (...), so filtering on licenses/payers/specialties
never multiplies rows (a JOIN would return a provider once per matching license/specialty).
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from booking.models import Provider, ProviderLicense, ProviderPayer, Specialty


@dataclass(frozen=True)
class SearchCriteria:
    state: str
    payer: str | None = None
    specialty: str | None = None
    accepting_new_patients_only: bool = True
    page: int = 1
    page_size: int = 10


def search_providers(db: Session, criteria: SearchCriteria, today: date) -> tuple[list[Provider], int]:
    stmt = select(Provider).where(
        Provider.licenses.any(
            (ProviderLicense.state == criteria.state) & (ProviderLicense.expires_on >= today)
        )
    )
    if criteria.payer:
        stmt = stmt.where(
            Provider.payers.any(func.lower(ProviderPayer.payer_name) == criteria.payer.lower())
        )
    if criteria.specialty:
        stmt = stmt.where(Provider.specialties.any(Specialty.slug == criteria.specialty))
    if criteria.accepting_new_patients_only:
        stmt = stmt.where(Provider.accepting_new_patients.is_(True))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page = db.scalars(
        stmt.order_by(
            Provider.rating.is_(None),  # False (has a rating) sorts first
            Provider.rating.desc(),
            Provider.last_name,
            Provider.first_name,
        )
        .offset((criteria.page - 1) * criteria.page_size)
        .limit(criteria.page_size)
    ).all()
    return list(page), total
