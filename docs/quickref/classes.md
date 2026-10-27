# Classes & dunder methods

```python
class Invoice:
    tax_rate = 0.1                       # class attribute (shared)

    def __init__(self, cents: int):     # constructor; `self` is always explicit
        self.cents = cents              # instance attribute (no declarations needed)

    @property
    def dollars(self) -> float:         # getter: inv.dollars (no parens)
        return self.cents / 100

    @classmethod
    def from_dollars(cls, d: float) -> "Invoice":   # alternative constructor
        return cls(round(d * 100))

    @staticmethod
    def helper(): ...                   # no self/cls

    def __repr__(self): return f"Invoice({self.cents})"      # debug / REPL text
    def __eq__(self, other):                                 # == (default compares identity)
        return isinstance(other, Invoice) and self.cents == other.cents
    def __add__(self, other): return Invoice(self.cents + other.cents)   # +
    def __lt__(self, other): return self.cents < other.cents             # < and sorting
```

Other dunders: `__str__` (str/print), `__len__`, `__iter__`, `__contains__` (`in`), `__hash__`, `__bool__`.

```python
class Child(Parent):
    def __init__(self, x):
        super().__init__(x)
```

`_name` = private by convention only. `isinstance(x, Cls)` ≈ `instanceof`.
⚠️ Defining `__eq__` sets `__hash__` to None (unhashable) unless you define it too.
