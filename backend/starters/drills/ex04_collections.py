"""Drill 04 - collections: defaultdict, Counter, and set operations.

TS mental model:
  - defaultdict(list) ~ a Map whose missing keys auto-initialize to []
  - Counter(items)    ~ items.reduce((acc, x) => (acc[x] = (acc[x] ?? 0) + 1, acc), {})
  - set operators: a - b (difference), a & b (intersection), a | b (union)

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen collections cheat sheet.
"""

from collections import Counter, defaultdict  # noqa: F401  (you will need these)


# ── Q1 · group_by_provider ───────────────────────────────────── fix the bug ──
# Each appointment is a dict with an "id" (int) and a "provider" (str).
# The daily schedule needs {provider: [appointment ids]}, with each provider's
# ids in input order.
#
#   group_by_provider([{"id": 1, "provider": "Lee"},
#                      {"id": 2, "provider": "Ng"},
#                      {"id": 3, "provider": "Lee"}])   -> {"Lee": [1, 3], "Ng": [2]}
#
# Use defaultdict(list) while building, but the returned value must be a
# plain dict (type(result) is dict), not a defaultdict.
# Today: raises KeyError the first time it sees a provider.
def group_by_provider(appointments: list[dict]) -> dict[str, list[int]]:
    groups = {}
    for appt in appointments:
        groups[appt["provider"]].append(appt["id"])
    return groups


# ── Q2 · top_diagnoses ─────────────────────────────────────────── implement ──
# The clinic dashboard shows the most frequent diagnosis codes.
# Return the `n` most common codes as (code, count) tuples, highest count
# first. When counts tie, the code that appeared first in `codes` comes first.
#
#   top_diagnoses(["F41.1", "F32.0", "F41.1", "F43.1", "F32.0", "F41.1"], 2)
#       -> [("F41.1", 3), ("F32.0", 2)]
#   top_diagnoses(["B", "A", "A", "B", "C"], 2)
#       -> [("B", 2), ("A", 2)]            tie: "B" was seen before "A"
#
# The result is a list of tuples, not a dict.
def top_diagnoses(codes: list[str], n: int) -> list[tuple[str, int]]:
    raise NotImplementedError


# ── Q3 · missing_fields ──────────────────────────────────────── fix the bug ──
# Before an intake form can be submitted, every name in `required` must have
# a value in `record`. Return the set of required names that are either
# absent from `record` OR present with the value None.
# Other falsy values (0, "", False) count as present.
#
#   missing_fields({"first_name": "Ann", "last_name": None},
#                  {"first_name", "last_name", "date_of_birth"})
#       -> {"last_name", "date_of_birth"}   None and absent both count
#   missing_fields({"copay_cents": 0, "notes": ""}, {"copay_cents", "notes"})
#       -> set()                            0 and "" are real values
#
# Don't mutate `record` or `required`.
# Today: only absent keys are reported; a key set to None is treated as filled.
def missing_fields(record: dict, required: set[str]) -> set[str]:
    return required - record.keys()


# ── Q4 · shared_patients ───────────────────────────────────────── implement ──
# Care coordination wants patients seen by BOTH providers. Each argument is a
# list of patient ids (may contain duplicates, any order).
# Return the ids that appear in both lists, each once, sorted ascending.
#
#   shared_patients([5, 1, 3, 3], [3, 5, 9])   -> [3, 5]   3 appears once
#   shared_patients([1], [2])                  -> []
#
# The result is a list, not a set.
def shared_patients(provider_a: list[int], provider_b: list[int]) -> list[int]:
    raise NotImplementedError
