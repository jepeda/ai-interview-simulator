"""Drill 05 - Functions and type hints (reference solution)."""


def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    return [*(tags or []), tag]


def format_name(
    first: str, last: str, *, middle: str | None = None, last_first: bool = False
) -> str:
    given = f"{first} {middle[0]}." if middle else first
    if last_first:
        return f"{last}, {given}"
    return f"{given} {last}"


def total_cents(*amounts: int, discount_pct: float = 0) -> int:
    return round(sum(amounts) * (1 - discount_pct / 100))


def build_query(path: str, **params: str | int | None) -> str:
    parts = [f"{key}={value}" for key, value in params.items() if value is not None]
    return f"{path}?{'&'.join(parts)}" if parts else path
