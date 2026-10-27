# Context managers: `with` (≈ try/finally, `using`)

```python
with open(path, encoding="utf-8") as f:     # closed even on exception
    text = f.read()
with Session(engine) as session, session.begin():   # commit, or rollback on error
    ...
```

**Write one with a generator** (simplest):
```python
from contextlib import contextmanager

@contextmanager
def timer(label):
    start = time.perf_counter()        # __enter__
    try:
        yield start                    # value bound by `as`
    finally:
        print(label, time.perf_counter() - start)   # __exit__, always runs
```

**Or as a class:**
```python
class Tx:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        ...                            # exc_type is None on success
        return False                   # True would SWALLOW the exception
```

`contextlib.suppress(KeyError)` ignores one exception type. `async with` is the async version.
