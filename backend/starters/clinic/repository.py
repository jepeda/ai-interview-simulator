"""Query functions. Routers call these; they return ORM objects."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from clinic.models import InsurancePlan, Patient


def list_patients(
    db: Session,
    *,
    payer: str | None = None,
    include_archived: bool = False,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[Patient], int]:
    """Return (patients for this page, total matching patients).

    - Every patient is listed, whether or not they have insurance.
    - Archived patients are hidden unless include_archived=True.
      (Legacy rows have status NULL - those are NOT archived.)
    - `payer` filters to patients whose plan's payer_name matches exactly.
    - Ordered by last_name, then first_name.
    """
    stmt = select(Patient).join(Patient.insurance_plan)

    if payer:
        stmt = stmt.where(InsurancePlan.payer_name == payer)
    if not include_archived:
        stmt = stmt.where(Patient.status != "archived")

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Patient.last_name, Patient.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total


def list_plans(db: Session) -> list[InsurancePlan]:
    return list(db.scalars(select(InsurancePlan).order_by(InsurancePlan.payer_name)).all())
