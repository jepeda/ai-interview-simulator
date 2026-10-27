# dataclasses & enums

```python
from dataclasses import dataclass, field, replace

@dataclass                                  # generates __init__, __repr__, __eq__
class Patient:
    name: str
    age: int = 0
    tags: list[str] = field(default_factory=list)   # ⚠️ never `= []`

    def __post_init__(self):                # validation after __init__
        if self.age < 0:
            raise ValueError("age must be >= 0")

p = Patient("Ana", 30)
p2 = replace(p, age=31)                     # ≈ {...p, age: 31}
```

| Option | Effect |
|---|---|
| `frozen=True` | immutable (assigning raises), and hashable |
| `order=True` | adds `<` etc. (compares fields in order) |
| `slots=True` | less memory, no new attributes |
| `kw_only=True` | keyword-only constructor |

Fields without defaults must come before fields with defaults.
`dataclasses.asdict(p)` → dict.

**Enums:**
```python
from enum import StrEnum, Enum, auto
class Status(StrEnum):           # members ARE strings: Status.ACTIVE == "active"
    ACTIVE = "active"
    INACTIVE = auto()            # "inactive"
Status("active")                 # lookup by value (ValueError if unknown)
Status.ACTIVE.value  Status.ACTIVE.name  list(Status)
```
