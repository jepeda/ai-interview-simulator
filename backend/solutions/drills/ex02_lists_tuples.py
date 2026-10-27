"""Drill 02 - Lists, tuples, slicing and unpacking (reference solution)."""


def first_and_last(items: list[str]) -> tuple[str, str] | None:
    if not items:
        return None
    return (items[0], items[-1])


def chunk(items: list[int], size: int) -> list[list[int]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def numbered(names: list[str], start: int = 1) -> list[str]:
    return [f"{i}. {name}" for i, name in enumerate(names, start=start)]


def pair_up(names: list[str], ids: list[int]) -> list[tuple[int, str]]:
    return list(zip(ids, names, strict=True))


def split_head_tail(values: list[int]) -> tuple[int, list[int]]:
    if not values:
        raise ValueError("values must not be empty")
    head, *tail = values
    return head, tail
