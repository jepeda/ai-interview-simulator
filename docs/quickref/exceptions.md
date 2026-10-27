# Exceptions

```python
try:
    amount = Decimal(raw)
except (InvalidOperation, ValueError) as e:   # catch specific types
    raise ValidationError(f"bad amount {raw!r}") from e   # keep the cause
else:
    ...          # ran only if no exception
finally:
    ...          # always
```

**Custom hierarchy:**
```python
class DomainError(Exception):
    def __init__(self, message: str, *, code: str):
        super().__init__(message)       # so str(e) == message
        self.code = code

class NotFound(DomainError): ...
```

| Common built-in | When |
|---|---|
| `KeyError` | `d["missing"]` |
| `IndexError` | `xs[99]` |
| `ValueError` | right type, bad value: `int("abc")` |
| `TypeError` | wrong type: `"a" + 1`, `None < 1` |
| `AttributeError` | `None.name` (≈ "cannot read properties of null") |

⚠️ Never bare `except:` or `except Exception: pass`: it hides bugs. `raise` alone re-raises the current error.

Tests: `with pytest.raises(NotFound, match="patient 7"):`
