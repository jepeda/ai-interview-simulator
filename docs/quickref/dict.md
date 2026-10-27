# dict: key → value (`Record` / `Map`)

```python
d = {"a": 1, "b": 2}            # keys: any hashable (str, int, tuple, frozenset)
d["a"]                          # 1, missing key → KeyError (not undefined!)
d.get("z")                      # None
d.get("z", 0)                   # 0              ≈ obj.z ?? 0
"a" in d                        # True (checks KEYS)  ≈ "a" in obj / map.has()
d["c"] = 3                      # add / overwrite
d.setdefault("e", []).append(1) # insert default if missing, return the value
del d["a"]; d.pop("b", None)    # remove (pop with default never raises)
len(d)
```

**Iterate** (insertion order is preserved):
```python
for k in d: ...                 # keys
for k, v in d.items(): ...      # ≈ Object.entries(obj)
list(d.keys()), list(d.values())
```

**Merge / copy** (new dict, later wins):
```python
{**a, **b}      a | b          # ≈ {...a, ...b}
a |= b          a.update(b)    # MUTATES a  ≈ Object.assign(a, b)
dict(a)         a.copy()       # shallow copy
```

**Build:** `dict(zip(keys, values))`, `{k: v for k, v in pairs}`, `dict.fromkeys(keys, 0)`

⚠️ Mutating a dict while iterating it → `RuntimeError`. Iterate over `list(d.items())` instead.
