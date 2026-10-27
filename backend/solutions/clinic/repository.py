"""Query functions (reference solution).

Fixes:
  - INNER JOIN -> OUTER JOIN, so patients without a plan are kept
  - `status != 'archived'` is NULL (not TRUE) for legacy rows where status IS NULL,
    so SQL drops them. Treat NULL explicitly.
"""

from sqlalchemy import func, or_, select
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
    stmt = select(Patient).outerjoin(Patient.insurance_plan)

    if payer:
        stmt = stmt.where(InsurancePlan.payer_name == payer)
    if not include_archived:
        stmt = stmt.where(or_(Patient.status.is_(None), Patient.status != "archived"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Patient.last_name, Patient.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total


def list_plans(db: Session) -> list[InsurancePlan]:
    return list(db.scalars(select(InsurancePlan).order_by(InsurancePlan.payer_name)).all())
