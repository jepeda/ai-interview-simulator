# Iteration helpers: any / all / next / generators

```python
any(p.overdue for p in patients)        # ≈ .some()
all(x > 0 for x in xs)                  # ≈ .every()   (all([]) is True)
next((p for p in ps if p.id == 7), None)  # ≈ .find() ?? null
sum(x.cents for x in items)             # ≈ reduce sum, sum([]) == 0
min(xs, default=None)  max(xs, key=len)
len([x for x in xs if cond])            # count matching
sum(1 for x in xs if cond)              # same, without the list
```

```python
enumerate(xs, start=1)      # (index, item)
zip(a, b)                   # pairs (strict=True to require equal length)
reversed(xs)  range(0, 10, 2)
from itertools import chain, islice, groupby, pairwise, batched
```

**Generators** are lazy and single-use:
```python
def evens(xs):
    for x in xs:
        if x % 2 == 0:
            yield x          # ≈ function* … yield
gen = (x for x in xs)        # generator expression
```
⚠️ Consuming a generator twice gives nothing the second time; wrap it in `list(...)` if you need it again.

`filter(fn, xs)` / `map(fn, xs)` exist but comprehensions are more idiomatic.
