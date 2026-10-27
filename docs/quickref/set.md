# set: unique, unordered, O(1) membership (`Set`)

```python
s = {1, 2, 3}           # literal (but {} is an empty DICT, use set())
s = set(xs)             # dedupe a list (order lost)
s.add(4); s.discard(9)  # discard never raises; remove() does
4 in s                  # ≈ s.has(4), O(1) vs O(n) for a list
```

**Set algebra** (operators return new sets):
```python
a | b     # union
a & b     # intersection
a - b     # difference (in a, not in b)
a ^ b     # symmetric difference
a <= b    # subset
```

**Order-preserving dedupe:** `list(dict.fromkeys(xs))`

`frozenset(...)` is immutable and hashable, so it can be a dict key.
