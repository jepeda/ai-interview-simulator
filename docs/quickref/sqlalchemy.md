# SQLAlchemy 2.0 (ORM)

```python
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id"))   # nullable
    plan: Mapped["Plan | None"] = relationship()
```

**Query:**
```python
stmt = (
    select(Patient)
    .where(Patient.state == "NY", Patient.active.is_(True))   # comma = AND
    .order_by(Patient.last_name, Patient.id.desc())
    .limit(20).offset(40)
)
session.scalars(stmt).all()          # list[Patient]
session.scalars(stmt).first()        # Patient | None
session.get(Patient, 7)              # by primary key, or None
session.scalar(select(func.count()).select_from(Patient))
```

**Joins:** `.join(Plan)` = INNER (drops patients with no plan!), `.outerjoin(Plan)` = LEFT.
**Filter on a related collection without duplicates:** `.where(Provider.licenses.any(License.state == "NY"))` (EXISTS)
**Case-insensitive:** `func.lower(col) == value.lower()`, or `col.ilike(value)`

**NULL:** `col.is_(None)` / `col.is_not(None)`. ⚠️ `col != "x"` does NOT match NULL rows (SQL three-valued logic):
use `or_(col != "x", col.is_(None))`.

**Write:** `session.add(obj); session.commit()`; `session.refresh(obj)` reloads from the DB.
