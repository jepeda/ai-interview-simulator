# list & tuple: sequences (`Array`)

**list**: mutable, ordered. **tuple**: immutable, ordered, hashable (can be a dict key / set member).

```python
xs = [3, 1, 2]
xs.append(4)            # push
xs.extend([5, 6])       # push(...arr)
xs.insert(0, 9)         # unshift-ish
xs.pop()  xs.pop(0)     # pop / shift (pop(0) is O(n), use deque for queues)
xs.remove(9)            # remove first matching VALUE (ValueError if absent)
xs.index(2)             # indexOf, but raises ValueError instead of -1
2 in xs                 # includes
len(xs)                 # .length
xs + [7]   [0] * 3      # concat / repeat (new lists)
```

**Indexing & slicing** `xs[start:stop:step]` (stop excluded, never raises):
```python
xs[0]  xs[-1]           # first / last  (≈ .at(-1))
xs[1:3]  xs[:2]  xs[2:] # slice → new list
xs[::-1]                # reversed copy
xs[:]                   # shallow copy  ≈ [...xs]
```

**Unpacking** (≈ destructuring):
```python
a, b = (1, 2)
first, *rest = xs       # ≈ const [first, ...rest] = xs
a, b = b, a             # swap
for i, x in enumerate(xs): ...          # ≈ xs.forEach((x, i) => …)
for a, b in zip(xs, ys): ...            # pairs, stops at the shorter
```

```python
point = (1, 2)          # tuple; (1,) is a 1-tuple, (1) is just 1
```

⚠️ `[[]] * 3` gives three references to the SAME list. Use `[[] for _ in range(3)]`.
