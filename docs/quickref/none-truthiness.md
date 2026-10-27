# None & truthiness

`None` is Python's only "nothing" (no `undefined`). Compare with **`is`**:
```python
if x is None: ...          # ✅
if x == None: ...          # works, but not idiomatic
```

**Falsy:** `None`, `False`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `()`
(unlike JS, **empty containers are falsy**; `"0"` and `"false"` are truthy)

```python
if not items: ...                    # empty or None
name = nickname or "anon"            # ≈ ||  (replaces "" and 0 too!)
name = nickname if nickname is not None else "anon"   # ≈ ??  (only None)
count = data.get("count") or 0
```

⚠️ `if patient.copay:` is False for a copay of `0`. Use `is not None` when 0 / "" are valid values.

No optional chaining: `x.y if x is not None else None`, or `getattr(x, "y", None)`.
`and`/`or` return one of their operands, not a bool.
