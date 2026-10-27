# Comprehensions: map + filter in one expression

```python
[f(x) for x in xs]                 # ≈ xs.map(f)
[x for x in xs if x > 0]           # ≈ xs.filter(x => x > 0)
[f(x) for x in xs if x > 0]        # filter THEN map
[a if cond else b for x in xs]     # conditional VALUE (if/else goes before `for`)

{k: v for k, v in pairs}           # dict comprehension
{x.lower() for x in names}         # set comprehension
(x * 2 for x in xs)                # generator: lazy, single-use
sum(x.price for x in items)        # generator straight into a function
```

**Nested** reads left-to-right like nested `for` loops:
```python
[cell for row in grid for cell in row]   # ≈ grid.flat()
```

Use a plain loop once it needs more than one `if`, or side effects.
