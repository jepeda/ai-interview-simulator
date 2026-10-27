"""Drill 02 - Lists, tuples, slicing and unpacking.

TS mental model:
  - list  ~ Array (mutable)          tuple ~ readonly fixed-length tuple
  - items[1:3] ~ items.slice(1, 3)   items[-1] ~ items.at(-1)
  - first, *rest = items  ~  const [first, ...rest] = items
  - for i, x in enumerate(items)  ~  items.forEach((x, i) => ...)
  - zip(a, b) pairs up two iterables (stops at the shortest by default)

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen list/tuple cheat sheet.
"""


# ── Q1 · first_and_last ──────────────────────────────────────── fix the bug ──
# The waitlist screen shows the first and the last patient name in the queue.
# Return a 2-tuple (first item, last item), or None when the list is empty.
#
#   first_and_last(["a", "b", "c"])   -> ("a", "c")
#   first_and_last(["solo"])          -> ("solo", "solo")   one item is both ends
#   first_and_last([])                -> None               no exception
#
# Today: returns ("b", "c") for ["a", "b", "c"], and raises IndexError for a
# one-item or empty list.
# TS equivalent: `items.length ? [items[0], items.at(-1)] : null`
def first_and_last(items: list[str]) -> tuple[str, str] | None:
    return (items[1], items[-1])


# ── Q2 · chunk ─────────────────────────────────────────────────── implement ──
# The claims batcher submits ids in batches of at most `size`.
# Split `items` into consecutive lists of length `size`, in the original
# order. The last chunk holds whatever is left over and may be shorter.
#
#   chunk([1, 2, 3, 4, 5], 2)   -> [[1, 2], [3, 4], [5]]   last chunk is short
#   chunk([1, 2, 3, 4], 2)      -> [[1, 2], [3, 4]]        no empty trailing chunk
#   chunk([], 3)                -> []
#
# Use slices (`size` is always >= 1). Don't mutate `items`.
def chunk(items: list[int], size: int) -> list[list[int]]:
    raise NotImplementedError


# ── Q3 · numbered ────────────────────────────────────────────── fix the bug ──
# The intake form lists patient names as a numbered list.
# Prefix each name with its position, counting from `start` (default 1),
# formatted as "<n>. <name>".
#
#   numbered(["Ann", "Bo"])             -> ["1. Ann", "2. Bo"]
#   numbered(["Ann", "Bo"], start=10)   -> ["10. Ann", "11. Bo"]
#
# Iterate with enumerate instead of range(len(...)).
# Today: numbering starts at 0 ("0. Ann") and `start` is ignored.
# TS equivalent: `names.map((n, i) => `${i + start}. ${n}`)`
def numbered(names: list[str], start: int = 1) -> list[str]:
    result = []
    for i in range(len(names)):
        result.append(f"{i}. {names[i]}")
    return result


# ── Q4 · pair_up ─────────────────────────────────────────────── fix the bug ──
# Two parallel lists from a CSV import: `names[i]` belongs to `ids[i]`.
# Return a list of (id, name) tuples - id FIRST, then name - in input order.
# If the two lists have different lengths, raise ValueError (data is corrupt).
#
#   pair_up(["Ann", "Bo"], [7, 9])   -> [(7, "Ann"), (9, "Bo")]
#   pair_up(["Ann", "Bo"], [7])      -> raises ValueError
#
# Today: tuples come out as (name, id), and a length mismatch silently drops
# the extra item instead of raising.
def pair_up(names: list[str], ids: list[int]) -> list[tuple[int, str]]:
    return list(zip(names, ids))


# ── Q5 · split_head_tail ───────────────────────────────────────── implement ──
# A visit's notes list: the first entry is the chief complaint, the rest are
# follow-up notes. Return a 2-tuple (first item, list of the remaining items).
#
#   split_head_tail([1, 2, 3])   -> (1, [2, 3])
#   split_head_tail([4])         -> (4, [])          the rest is an empty LIST
#   split_head_tail([])          -> raises ValueError
#
# Use star-unpacking. The second element must be a list, not a tuple.
# TS equivalent: `const [head, ...tail] = values; return [head, tail]`
def split_head_tail(values: list[int]) -> tuple[int, list[int]]:
    raise NotImplementedError
