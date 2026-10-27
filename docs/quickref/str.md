# str: immutable text

```python
s.strip()  s.lstrip()  s.rstrip()        # trim (or strip("x") for chars)
s.lower()  s.upper()  s.title()  s.casefold()
s.split()                                # on any whitespace, drops empties
s.split(",")                             # exact separator
", ".join(names)                         # ≈ names.join(", ")  (join is on the SEPARATOR, items must be str)
s.replace("a", "b")                      # replaces ALL (≈ replaceAll)
s.startswith("Dr.")  s.endswith((".py", ".ts"))
"sub" in s                               # ≈ includes
s.find("x")  # -1 if missing     s.index("x")  # raises
s.removeprefix("Dr. ")  s.removesuffix("!")
s.isdigit()  s.isalpha()  s.isspace()
s[0]  s[-3:]  s[::-1]                    # slicing works like lists
```

**f-strings** (≈ template literals):
```python
f"{name} owes ${cents / 100:.2f}"        # 2 decimals
f"{n:,}"            # 1,234,567
f"{n:05d}"          # 00042 (zero-pad)
f"{pct:.1%}"        # 12.5%
f"{name:<10}|"      # left-align in 10 chars (> right, ^ center)
f"{value!r}"        # repr(): quotes strings
f"{x=}"             # debug: "x=42"
```

Building in a loop: append to a list and `"".join(parts)` at the end.
