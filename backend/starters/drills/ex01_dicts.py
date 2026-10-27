"""Drill 01 - Dictionaries.

TS mental model: a dict is like a `Record<string, T>` or `Map<K, V>`, BUT
`d["missing"]` raises KeyError instead of returning `undefined`.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen dict cheat sheet.
"""


# ── Q1 · get_copay_cents ─────────────────────────────────────── fix the bug ──
# `plan` is an insurance plan record from the billing API. Its "copay_cents"
# key is optional: some plans have no copay at all.
#
# Return plan["copay_cents"], or 0 when the key is missing.
#
#   get_copay_cents({"copay_cents": 2500})   -> 2500
#   get_copay_cents({"copay_cents": 0})      -> 0      a real 0 is still 0
#   get_copay_cents({})                      -> 0      today: raises KeyError
#
# TS equivalent: `plan.copay_cents ?? 0`. Do it without try/except.
def get_copay_cents(plan: dict) -> int:
    return plan["copay_cents"]


# ── Q2 · count_by_status ─────────────────────────────────────── fix the bug ──
# Each appointment is a dict with a "status" key ("scheduled", "cancelled", ...).
# Return how many appointments have each status.
#
#   count_by_status([{"status": "scheduled"},
#                    {"status": "cancelled"},
#                    {"status": "scheduled"}])   -> {"scheduled": 2, "cancelled": 1}
#   count_by_status([])                          -> {}
#
# Only statuses that actually appear are keys (no zero counts).
# Today: raises KeyError the first time it sees a status.
def count_by_status(appointments: list[dict]) -> dict[str, int]:
    counts = {}
    for appt in appointments:
        counts[appt["status"]] += 1
    return counts


# ── Q3 · merge_preferences ───────────────────────────────────── fix the bug ──
# A user's settings = the app `defaults`, with the user's `overrides` on top.
# Return a NEW dict containing every key from both; when a key is in both,
# the value from `overrides` wins.
#
#   merge_preferences({"theme": "light", "tz": "UTC"}, {"theme": "dark"})
#       -> {"theme": "dark", "tz": "UTC"}
#
# Neither argument may change: callers reuse `defaults` for every user.
# Today: returns the right value but corrupts `defaults` (it mutates it).
# TS equivalent: `{ ...defaults, ...overrides }`
def merge_preferences(defaults: dict, overrides: dict) -> dict:
    defaults.update(overrides)
    return defaults


# ── Q4 · invert_index ─────────────────────────────────────────── implement ──
# The scheduler keeps a provider name -> list of their patient ids.
# The front desk needs the reverse: patient id -> provider name.
#
#   invert_index({"Dr. Lee": [1, 2], "Dr. Ng": [3]})
#       -> {1: "Dr. Lee", 2: "Dr. Lee", 3: "Dr. Ng"}
#   invert_index({"Dr. Lee": []})   -> {}       a provider with no patients adds nothing
#
# Each patient has exactly one provider. Keys of the result are ints.
def invert_index(patient_ids_by_provider: dict[str, list[int]]) -> dict[int, str]:
    raise NotImplementedError
