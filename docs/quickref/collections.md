# collections: defaultdict, Counter, deque

```python
from collections import defaultdict, Counter, deque
```

**defaultdict**: missing keys are created on first access.
```python
groups = defaultdict(list)
for p in patients:
    groups[p.state].append(p)      # no "if key not in" check
counts = defaultdict(int)          # int() == 0
counts["x"] += 1
dict(groups)                       # convert back for output / equality
```

**Counter**: a dict of counts.
```python
c = Counter(["a", "b", "a"])       # Counter({'a': 2, 'b': 1})
c["zzz"]                           # 0 (no KeyError)
c.most_common(2)                   # [('a', 2), ('b', 1)]
c.update(more_items); c1 + c2      # add counts
```

**deque**: O(1) at both ends (queues, sliding windows).
```python
q = deque([1, 2]); q.append(3); q.popleft()
deque(maxlen=3)                    # keeps only the last 3
```

Also: `namedtuple("Point", "x y")` (a lightweight record; prefer `@dataclass` today).
