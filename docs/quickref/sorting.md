# Sorting

```python
sorted(xs)                     # NEW list (≈ [...xs].sort())
xs.sort()                      # in place, returns None (don't assign it!)
sorted(xs, reverse=True)
sorted(people, key=lambda p: p.last_name)        # key fn, not a comparator
sorted(people, key=lambda p: (p.last, p.first))  # multi-key: tuples compare left to right
sorted(nums, key=lambda n: (-n.score, n.name))   # score desc, name asc (negate numbers)
min(xs, key=len)  max(d, key=d.get)              # same key= idea
```

`from operator import attrgetter, itemgetter`: `key=itemgetter("date")` ≈ `lambda r: r["date"]`

**None values:** comparing `None < 1` raises TypeError. Put them last with:
```python
sorted(xs, key=lambda p: (p.rating is None, p.rating or 0))   # False < True
```

**Mixed directions on strings** (can't negate): sort twice, least important key first. `sort` is stable.

⚠️ Sorting date *strings* is only correct for ISO `YYYY-MM-DD`; "3/10/2026" sorts wrong. Parse to `date`/`datetime` first.
