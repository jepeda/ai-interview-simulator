# Type hints (checked by your editor / mypy, NOT at runtime)

```python
x: int = 1
names: list[str]              # string[]
ages: dict[str, int]          # Record<string, number>
pair: tuple[int, str]         # [number, string]
many: tuple[int, ...]         # number[] that's immutable
maybe: str | None = None      # string | null   (old style: Optional[str])
either: int | str
from typing import Any, Literal, TypedDict, Callable, Iterable
status: Literal["active", "inactive"]
cb: Callable[[int, str], bool]   # (a: number, b: string) => boolean
```

```python
def first[T](xs: list[T]) -> T | None: ...   # generics (3.12 syntax)
type UserId = int                             # type alias (3.12)
```

Prefer `Iterable[T]` / `Sequence[T]` / `Mapping[K, V]` for parameters (accept anything list-like).

Pydantic and FastAPI DO read hints at runtime: they validate and convert with them.
