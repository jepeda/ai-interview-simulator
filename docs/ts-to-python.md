# TypeScript → Python cheat sheet

Written for someone who thinks in TS/Node, aimed at the Python you'll write in a FastAPI interview.
Python 3.12+ syntax throughout.

## Basics

| TypeScript | Python | Notes |
|---|---|---|
| `const x = 1; let y = 2` | `x = 1` | No declarations. `UPPER_CASE` signals "constant" by convention only. |
| `// comment`, `/* */` | `# comment`, `"""docstring"""` | A string literal as the first statement of a function/class/module is its docstring. |
| `{ ... }` blocks | indentation + `:` | 4 spaces. Mixing tabs and spaces is an error. |
| `true / false / null / undefined` | `True / False / None` | There's only one "nothing": `None`. |
| `&&  \|\|  !` | `and  or  not` | `and`/`or` return an operand, like JS. |
| `===` / `!==` | `==` / `!=` | `==` is value equality (calls `__eq__`). |
| `a === b` (same object) | `a is b` | Use `is` only for `None`, `True`, `False`, and identity checks. |
| `cond ? a : b` | `a if cond else b` | |
| `x ?? fallback` | `x if x is not None else fallback` | ⚠️ `x or fallback` also replaces `0`, `""`, `[]`. |
| `a?.b?.c` | no operator | `(a or {}).get("b")`, or explicit `if a is not None`. |
| `typeof x === "string"` | `isinstance(x, str)` | |
| `` `Hi ${name}` `` | `f"Hi {name}"` | |
| `console.log(x)` | `print(x)` | `print(f"{x=}")` prints `x=<value>`, handy for debugging. |
| `i++` | `i += 1` | No `++` or `--`. |
| `Math.floor(a / b)` | `a // b` | `/` always returns a float. `%` is modulo, `**` is power. |
| `Number("42")`, `parseInt` | `int("42")`, `float("4.2")` | Raises `ValueError` on bad input, unlike JS's NaN. |
| `String(42)` | `str(42)` | |

## Truthiness (different from JS!)

Falsy: `None`, `False`, `0`, `0.0`, `""`, **`[]`, `{}`, `set()`**, and anything with `__len__() == 0`.

```python
if not items:            # empty list → True (in JS, [] is truthy!)
if copay is None:        # explicit None check: 0 is a valid copay
if value:                # ⚠️ skips 0 and "" too
```

## Strings

| TypeScript | Python |
|---|---|
| `s.length` | `len(s)` |
| `s.trim()`, `trimStart()` | `s.strip()`, `s.lstrip()` |
| `s.toUpperCase()` | `s.upper()` |
| `s.includes("x")` | `"x" in s` |
| `s.startsWith("x")` | `s.startswith("x")` |
| `s.replace(/-/g, "")` | `s.replace("-", "")` (replaces ALL by default) |
| `s.split(",")` | `s.split(",")`; `s.split()` splits on any whitespace run |
| `arr.join(", ")` | `", ".join(arr)` (items must be `str`) |
| `s.slice(1, 3)`, `s.at(-1)` | `s[1:3]`, `s[-1]` |
| `n.toFixed(2)` | `f"{n:.2f}"` |
| `n.toLocaleString()` | `f"{n:,}"` |
| `String(n).padStart(6, "0")` | `f"{n:06d}"` or `str(n).zfill(6)` |
| `s.repeat(3)` | `s * 3` |
| `/^\d+$/.test(s)` | `re.fullmatch(r"\d+", s)` (`import re`) or `s.isdigit()` |
| multi-line template | `"""triple quoted"""` |

## Lists (arrays)

| TypeScript | Python |
|---|---|
| `[1, 2, 3]` | `[1, 2, 3]` |
| `arr.length` | `len(arr)` |
| `arr.push(x)` | `arr.append(x)` |
| `arr.push(...more)` | `arr.extend(more)` |
| `arr.pop()` / `arr.shift()` | `arr.pop()` / `arr.pop(0)` (use `collections.deque` for queues) |
| `arr.includes(x)` | `x in arr` |
| `arr.indexOf(x)` | `arr.index(x)` (raises `ValueError` if missing) |
| `arr.slice(1, -1)` | `arr[1:-1]` |
| `[...arr]` | `arr.copy()` or `list(arr)` or `arr[:]` |
| `[...a, ...b]` | `[*a, *b]` or `a + b` |
| `arr.reverse()` (in place) | `arr.reverse()`; copy: `arr[::-1]` or `list(reversed(arr))` |
| `const [a, b] = pair` | `a, b = pair` |
| `const [first, ...rest] = arr` | `first, *rest = arr` |
| `arr.forEach((x, i) => ...)` | `for i, x in enumerate(arr):` |
| `for (let i = 0; i < n; i++)` | `for i in range(n):` |
| `Array.from({length: n}, (_, i) => i)` | `list(range(n))` |
| zip two arrays | `for a, b in zip(xs, ys, strict=True):` |

**Tuples** `(1, "a")` are immutable lists, often used for fixed-shape records and multiple return values: `return total, errors`.

## map / filter / reduce → comprehensions

```python
emails = [p.email.lower() for p in patients if p.active]           # filter + map
by_id  = {p.id: p for p in patients}                                # Object.fromEntries
payers = {plan.payer for plan in plans}                             # new Set(...)
codes  = [c for visit in visits for c in visit.codes]               # flatMap
total  = sum(s.minutes for s in sessions if s.billable)             # reduce(sum)  (generator: no [])
first  = next((p for p in patients if p.id == pid), None)           # find(...) ?? null
any(p.overdue for p in invoices)   /   all(c.verified for c in claims)   # some / every
```

`map(fn, xs)` and `filter(fn, xs)` exist but return lazy iterators. Comprehensions are more idiomatic.

## Dicts (objects / Maps)

| TypeScript | Python |
|---|---|
| `{ a: 1, "b-c": 2 }` | `{"a": 1, "b-c": 2}` (keys are quoted, any hashable type) |
| `obj.a` / `obj["a"]` | `d["a"]`: ⚠️ raises `KeyError` if missing |
| `obj.a ?? 0` | `d.get("a", 0)` |
| `"a" in obj` | `"a" in d` |
| `delete obj.a` | `del d["a"]` or `d.pop("a", None)` |
| `Object.keys / values / entries` | `d.keys()`, `d.values()`, `d.items()` |
| `for (const [k, v] of Object.entries(o))` | `for k, v in d.items():` |
| `{ ...a, ...b }` | `{**a, **b}` or `a \| b` |
| `Object.assign(a, b)` (mutates) | `a.update(b)` |
| `obj[k] = obj[k] ?? []` | `d.setdefault(k, [])` or `collections.defaultdict(list)` |
| count occurrences | `collections.Counter(items)`, `.most_common(3)` |
| `JSON.stringify / parse` | `json.dumps(d)` / `json.loads(s)` |

Dicts preserve insertion order, like JS objects with string keys.

## Sets

`s = {1, 2}` (careful: `{}` is an empty **dict**, so write `set()`). Operators: `a | b` union, `a & b` intersection, `a - b` difference, `x in s`.

## Sorting

```python
sorted(items)                                         # new list (like [...items].sort())
items.sort()                                          # in place, returns None (!)
sorted(patients, key=lambda p: p.last_name.lower())   # key function, not comparator
sorted(rows, key=lambda r: (r.last, r.first))         # multi-column: tuple key
sorted(providers, key=lambda p: (-p.rating, p.name))  # mixed direction: negate numbers
sorted(xs, key=lambda x: x.created_at, reverse=True)  # newest first
sorted(plans, key=lambda p: (p.end is None, p.end or date.min))  # None last
```

⚠️ Sort dates as `date`/`datetime` objects, never as formatted strings like `"01/05/2027"`.

## Functions

```python
def greet(name: str, greeting: str = "Hi") -> str:          # defaults
    return f"{greeting}, {name}"

def fmt(first: str, last: str, *, middle: str | None = None) -> str: ...   # after * → keyword-only
fmt("Ada", "King", middle="B")

def total(*amounts: int) -> int:        # (...amounts: number[])  → tuple
    return sum(amounts)

def query(path: str, **params: str) -> str:   # arbitrary named args → dict
    ...

total(*[1, 2, 3])      # spread a list into args
query("/p", **filters) # spread a dict into keyword args

square = lambda x: x * x          # single expression only. Prefer def for anything real.
```

⚠️ **Mutable default arguments** are evaluated once and shared between calls:

```python
def add(tag, tags=[]):        # BUG: the same list every call
def add(tag, tags=None):      # ✓ then: tags = [] if tags is None else tags
```

Closures work like JS, but to *reassign* an outer variable you need `nonlocal x` (or `global x`).

## Type hints

| TypeScript | Python |
|---|---|
| `string, number, boolean` | `str`, `int` / `float`, `bool` |
| `string[]` | `list[str]` |
| `Record<string, number>` | `dict[str, int]` |
| `[number, string]` | `tuple[int, str]`; variable length: `tuple[int, ...]` |
| `Set<string>` | `set[str]` |
| `string \| null` | `str \| None` (older code: `Optional[str]`) |
| `any` / `unknown` | `Any` / `object` |
| `(x: number) => string` | `Callable[[int], str]` (`from collections.abc import Callable`) |
| `"a" \| "b"` | `Literal["a", "b"]` |
| `type ID = number` | `type ID = int` (3.12) or `ID = int` |
| `interface User {...}` | `TypedDict`, `@dataclass`, or a Pydantic `BaseModel` |
| generics `<T>` | `def first[T](xs: list[T]) -> T:` (3.12) |
| `Promise<T>` | `async def f() -> T` (or `Awaitable[T]`) |

Hints are **not enforced at runtime** (except by Pydantic/FastAPI). Use Pylance or mypy to check them.

## None handling

```python
if user is None: ...                  # not `== None`
name = user.name if user else "Guest"
phone = (patient.get("contact") or {}).get("phone")   # optional-chaining substitute
member_id = (raw or "").strip() or "SELF-PAY"          # blank-or-None → default
```

## Classes

```python
class Money:
    currency = "USD"                       # class attribute (shared, like static)

    def __init__(self, cents: int) -> None:   # constructor. self is explicit, ALWAYS
        self.cents = cents                    # instance attribute

    @property
    def dollars(self) -> float:            # get dollars() {}
        return self.cents / 100

    @classmethod
    def from_dollars(cls, d: str) -> "Money":   # static factory (cls = the class)
        return cls(int(Decimal(d) * 100))

    @staticmethod
    def zero() -> "Money": ...             # static method, no self/cls

    def __repr__(self) -> str: return f"Money({self.cents})"   # debug representation
    def __str__(self) -> str: return f"${self.cents/100:,.2f}"  # toString()
    def __eq__(self, other: object) -> bool: ...                # ==  (default: identity)
    def __add__(self, other: "Money") -> "Money": ...           # +
    def __len__(self) -> int: ...                               # len(x), truthiness

class Child(Parent):
    def __init__(self, x):
        super().__init__(x)
```

Private: `_name` by convention. `__name` mangles the name. Nothing is truly private.
Interfaces: `typing.Protocol` (structural, like TS) or `abc.ABC` (nominal).

## Dataclasses, enums & Pydantic

```python
from dataclasses import dataclass, field, replace, asdict

@dataclass                         # generates __init__, __repr__, __eq__
class Appointment:
    provider: str
    starts_at: datetime
    duration: int = 50
    tags: list[str] = field(default_factory=list)   # never `= []`

@dataclass(frozen=True)            # immutable + hashable (usable as dict key / in sets)
class PlanKey: payer: str; code: str

updated = replace(appt, duration=90)   # { ...appt, duration: 90 }
asdict(appt)                           # → dict

from enum import StrEnum
class Status(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
Status("active") is Status.ACTIVE; Status.ACTIVE == "active"   # True, True
```

**Pydantic** (FastAPI's request/response models) ≈ **zod schema + TS type in one**:

```python
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

class PatientIn(BaseModel):
    name: str = Field(min_length=1)
    dob: date                         # parses "1990-04-12" → date; bad input → 422
    member_id: str | None = None      # optional needs a default!

    @field_validator("dob")
    @classmethod
    def not_future(cls, v: date) -> date:
        if v > date.today(): raise ValueError("in the future")
        return v

    @model_validator(mode="after")    # cross-field rules
    def check(self) -> "PatientIn": ...; return self

class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # build from ORM objects
    id: int

PatientIn.model_validate({"name": "Ada", "dob": "1990-04-12"})   # zod .parse()
patient.model_dump()  /  patient.model_dump_json()                 # → dict / JSON
```

## Exceptions

```python
try:
    value = int(raw)
except ValueError as err:          # catch (e) — but by TYPE
    raise BadInput(f"bad {raw!r}") from err      # error cause chaining
except (KeyError, TypeError):
    ...
else:
    ...                            # ran only if no exception
finally:
    ...

class ClinicError(Exception): ...
class EligibilityError(ClinicError):
    def __init__(self, patient_id: int):
        super().__init__(f"Patient {patient_id} not eligible")
        self.patient_id = patient_id
```

Common built-ins: `ValueError` (bad value), `TypeError` (wrong type), `KeyError` (dict),
`IndexError` (list), `AttributeError` (`x.missing`), `NotImplementedError`.
In FastAPI: `raise HTTPException(status_code=404, detail="Not found")`.

## Context managers (`with`)

Like `try/finally` or `using` in C# and TS 5.2:

```python
with open(path, encoding="utf-8") as f:     # file closed automatically
    data = f.read()

with SessionLocal() as db: ...              # SQLAlchemy session closed

from contextlib import contextmanager
@contextmanager
def timer(label):
    start = time.perf_counter()
    try:
        yield                                # the with-block runs here
    finally:
        print(label, time.perf_counter() - start)
```

## async / await

| TypeScript | Python |
|---|---|
| `async function f() {}` | `async def f(): ...` |
| `await p` | `await coro` |
| `f()` without await | Returns a coroutine that **never runs** (no work starts!) |
| `Promise.all([a(), b()])` | `await asyncio.gather(a(), b())` |
| `Promise.allSettled(...)` | `await asyncio.gather(*coros, return_exceptions=True)` |
| `Promise.race` / timeout | `async with asyncio.timeout(2): ...` or `await asyncio.wait_for(coro, 2)` |
| `setTimeout` sleep | `await asyncio.sleep(0.5)` |
| p-limit | `sem = asyncio.Semaphore(5)` + `async with sem:` |
| top-level entry | `asyncio.run(main())` |

FastAPI: `async def` endpoints run on the event loop, so **never call blocking I/O inside them**
(sync SQLAlchemy, `requests`, `time.sleep`). Plain `def` endpoints run in a threadpool and are safe for blocking code.

## Modules & imports

```python
import json                                  # import * as json from "json"
from datetime import date, datetime          # import { date, datetime } from ...
from clinic.services import eligibility      # package path = folders with modules
from .models import Patient                  # relative import (inside a package)
import numpy as np                           # alias

if __name__ == "__main__":                   # "run only when executed directly"
    main()
```

There's no `export`: every top-level name is importable. A leading `_` means "internal".

## Dates & times

```python
from datetime import date, datetime, timedelta, UTC
date.today(); datetime.now(UTC)
date(2026, 10, 26) + timedelta(days=7)
date.fromisoformat("2026-10-26"); d.isoformat()
dt.strftime("%m/%d/%Y %I:%M %p")              # format (display only!)
datetime.strptime("10/26/2026", "%m/%d/%Y")   # parse
(d2 - d1).days
```

⚠️ Don't compare naive and timezone-aware datetimes. That raises `TypeError`.

## FastAPI ↔ Express

```python
app = FastAPI()
router = APIRouter(prefix="/patients")               # express.Router()

@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int,                     # path param (typed + validated)
                include_archived: bool = False,      # query param: ?include_archived=true
                db: Session = Depends(get_db)):      # dependency injection (middleware-ish)
    ...

@router.post("", status_code=201)
def create(payload: PatientIn): ...                  # JSON body validated by Pydantic → 422 on error

app.include_router(router)
```

- Validation errors are automatic **422** responses with `detail: [{loc, msg, type}]`.
- Interactive docs at `/docs` (Swagger) for free.
- Tests: `TestClient(app).get("/patients")` (like supertest); override deps with `app.dependency_overrides[get_db] = ...`.

## SQLAlchemy 2.0 ↔ Prisma / TypeORM

```python
class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id"))   # nullable via | None
    plan: Mapped[Plan | None] = relationship()

stmt = (select(Patient)
        .outerjoin(Patient.plan)                 # .join() = INNER JOIN, which drops unmatched rows!
        .where(Patient.status.is_(None) | (Patient.status != "archived"))
        .order_by(Patient.last_name)
        .offset(20).limit(10))
patients = db.scalars(stmt).all()
patient = db.get(Patient, 42)                    # by primary key, or None
db.add(p); db.commit(); db.refresh(p)
```

⚠️ SQL NULL: `col != 'x'` is NULL (not true) when `col` is NULL. Use `.is_(None)` explicitly.

## pytest ↔ Jest

```python
def test_total():                                # any function named test_*
    assert total(1, 2) == 3                      # plain assert; pytest shows a rich diff

def test_raises():
    with pytest.raises(ValueError, match="bad"):
        parse("x")

@pytest.mark.parametrize(("raw", "expected"), [("1", 1), ("2", 2)])   # test.each
def test_parse(raw, expected): ...

@pytest.fixture                                  # beforeEach + dependency injection
def client(): yield TestClient(app)              # code after yield = teardown
def test_api(client): ...                        # requested by parameter name
```

Run: `uv run pytest path/to/test_file.py -k name_substring -x -vv`.

## Tooling ↔ npm

| Node | Python (this repo) |
|---|---|
| `package.json` | `pyproject.toml` |
| `npm install` | `uv sync` (creates `.venv`) |
| `npm install pkg` | `uv add pkg` |
| `npx tool` | `uv run tool` |
| `node_modules/` | `.venv/` |
| `nvm` | `uv python install 3.12` |
| ESLint + Prettier | `ruff check` + `ruff format` |
| `tsc --noEmit` | `mypy` / Pylance (VS Code) |

## Interview gotchas checklist

- `d["k"]` raises KeyError. Use `.get()` when the key may be absent.
- `if x:` is false for `0`, `""`, `[]`. Use `is None` when you mean None.
- Mutable defaults (`=[]`, `={}`) are shared across calls.
- `list.sort()` returns `None`. `sorted()` returns a new list.
- An un-awaited coroutine does nothing (you'll see "coroutine was never awaited").
- An integer division surprise: `7 / 2 == 3.5` and `7 // 2 == 3`.
- `round(2.5) == 2` (banker's rounding). Use `Decimal` for money.
- Copying: `b = a` aliases. Use `a.copy()` (shallow) or `copy.deepcopy(a)`.
- Strings are immutable: `s.upper()` returns a new string, so assign it.
- Late-binding closures in loops: `lambda i=i: i` captures the current value.
