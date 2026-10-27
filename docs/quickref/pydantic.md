# Pydantic v2 (≈ zod): request/response models

```python
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, AwareDatetime

class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str | None = None             # optional AND nullable
    age: int = Field(ge=0, le=130)
    tags: list[str] = []                 # mutable defaults are fine here (copied)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name is blank")     # ValueError → 422, never a 500
        return v

    @model_validator(mode="after")
    def check_dates(self):                         # cross-field rules
        if self.end < self.start:
            raise ValueError("end before start")
        return self
```

```python
PatientCreate.model_validate(data)        # ≈ schema.parse(), raises ValidationError
p.model_dump()   p.model_dump(exclude_unset=True)   # PATCH: only fields the client sent
p.model_copy(update={"age": 31})
class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # build from ORM objects
Out.model_validate(orm_obj)
```

Pydantic **coerces** by default: `"5"` → `5` for an `int` field. `Field(strict=True)` to refuse.
⚠️ Raise `ValueError`/`AssertionError` in validators. Other exceptions escape as 500s.
