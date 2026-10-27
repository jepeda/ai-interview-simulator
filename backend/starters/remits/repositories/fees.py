from sqlalchemy import select
from sqlalchemy.orm import Session

from remits.models import FeeSchedule


def contracted_allowed(db: Session, payer: str, cpt_code: str) -> int | None:
    """The allowed amount in cents our contract with `payer` sets for `cpt_code`, if any."""
    stmt = select(FeeSchedule.allowed_cents).where(
        FeeSchedule.payer == payer, FeeSchedule.cpt_code == cpt_code
    )
    return db.scalar(stmt)


def fee_table(db: Session) -> dict[tuple[str, str], int]:
    """{(payer, cpt_code): allowed_cents} for every contract."""
    return {(f.payer, f.cpt_code): f.allowed_cents for f in db.scalars(select(FeeSchedule))}
