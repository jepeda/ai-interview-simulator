# Functions & arguments

```python
def book(patient_id: int, *, notify: bool = True, note: str | None = None) -> str:
    ...
book(1, notify=False)            # everything after `*` is keyword-only
```

| Syntax | Meaning | TS analogue |
|---|---|---|
| `def f(a, b=2)` | default value | `b = 2` |
| `def f(*args)` | extra positionals → tuple | `...args` |
| `def f(**kwargs)` | extra keywords → dict | an options object |
| `def f(a, /, b)` | `a` positional-only | none |
| `f(*xs, **opts)` | spread into a call | `f(...xs)` |

⚠️ **Mutable default arguments are shared between calls:**
```python
def add(x, into=[]):   # BUG: one list for every call
def add(x, into=None):
    into = [] if into is None else into
```

```python
lambda x: x * 2                  # single expression only
from functools import partial, cache
```

Functions are values: pass them, return them, store them in dicts.
