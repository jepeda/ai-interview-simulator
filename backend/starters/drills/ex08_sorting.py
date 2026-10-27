"""Drill 08 - Sorting.

TS mental model: instead of a comparator `(a, b) => number`, Python sorts by a
KEY function `x => valueToCompare`. sorted(items, ...) returns a NEW list like
`[...items].sort(...)`; items.sort(...) sorts in place and returns None.
Python's sort is stable: equal keys keep their original order.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen sorting cheat sheet.
"""

from datetime import date, datetime  # noqa: F401


# ── Q1 · sort_by_name ────────────────────────────────────────── fix the bug ──
# The patient roster shows patients alphabetically. Each patient is a dict
# with "first_name" and "last_name". Return them sorted by last name, then by
# first name when last names tie, ignoring upper/lower case.
#
#   sort_by_name([{"first_name": "zoe", "last_name": "smith"},
#                 {"first_name": "Al",  "last_name": "Smith"},
#                 {"first_name": "Bea", "last_name": "adams"}])
#       -> [Bea adams, Al Smith, zoe smith]   "smith" == "Smith", so first name decides
#
# Return a NEW list. The caller's list must keep its original order.
# Return the original dicts unchanged (don't lowercase the names you return).
# Today: case-sensitive ("Smith" sorts before "adams"), no first-name
# tiebreak, and it reorders the caller's list.
def sort_by_name(patients: list[dict]) -> list[dict]:
    patients.sort(key=lambda p: p["last_name"])
    return patients


# ── Q2 · newest_first ──────────────────────────────────────────── implement ──
# The chart view lists clinical notes with the most recent on top. Each note
# has a "created_at" datetime. Return the notes sorted newest -> oldest.
#
#   newest_first([{"id": 1, "created_at": datetime(2026, 1, 5, 9, 0)},
#                 {"id": 2, "created_at": datetime(2026, 3, 1, 8, 0)},
#                 {"id": 3, "created_at": datetime(2025, 12, 31, 23, 59)}])
#       -> notes in id order [2, 1, 3]
#
# datetimes compare with < and > just like numbers.
# TS equivalent: [...notes].sort((a, b) => b.createdAt - a.createdAt)
def newest_first(notes: list[dict]) -> list[dict]:
    raise NotImplementedError


# ── Q3 · by_termination_date ─────────────────────────────────── fix the bug ──
# Insurance plans have a "termination_date": a date, or None if the plan has
# no end date. Show plans ending soonest first; open-ended plans go LAST.
#
#   by_termination_date([{"id": "open",  "termination_date": None},
#                        {"id": "late",  "termination_date": date(2027, 1, 1)},
#                        {"id": "early", "termination_date": date(2026, 6, 30)},
#                        {"id": "open2", "termination_date": None}])
#       -> ids ["early", "late", "open", "open2"]
#
# Plans that are both None keep their input order ("open" before "open2").
# Today: raises TypeError ("'<' not supported between ... 'date' and
# 'NoneType'"); unlike JS, Python refuses to compare None with a date.
def by_termination_date(plans: list[dict]) -> list[dict]:
    return sorted(plans, key=lambda p: p["termination_date"])


# ── Q4 · rank_providers ────────────────────────────────────────── implement ──
# The "find a therapist" page ranks providers. Each provider is
# {"name": str, "rating": float}. Return just the NAMES, best rating first;
# providers with equal ratings are ordered by name A-Z.
#
#   rank_providers([{"name": "Ng",   "rating": 4.5},
#                   {"name": "Lee",  "rating": 4.9},
#                   {"name": "Diaz", "rating": 4.5},
#                   {"name": "Ames", "rating": 3.0}])
#       -> ["Lee", "Diaz", "Ng", "Ames"]   Diaz and Ng tie at 4.5: A-Z
#
# Note the two directions: rating descending, name ascending.
def rank_providers(providers: list[dict]) -> list[str]:
    raise NotImplementedError
