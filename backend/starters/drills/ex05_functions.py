"""Drill 05 - Functions and type hints.

TS mental model:
  function f(a: string, opts?: { middle?: string })   -> def f(a: str, *, middle: str | None = None)
  function sum(...nums: number[])                      -> def total(*nums: int)
  function q(params: Record<string, unknown>)          -> def q(**params: object)

Python gotcha: default values are evaluated ONCE, at definition time.
A `[]` default is shared between every call.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen functions cheat sheet.
"""


# ── Q1 · add_tag ─────────────────────────────────────────────── fix the bug ──
# Appointments carry tags like "intake" or "urgent". Return a list that is
# `tags` with `tag` appended at the end.
#
#   add_tag("intake")               -> ["intake"]
#   add_tag("followup")             -> ["followup"]           every call starts fresh
#   add_tag("urgent", ["intake"])   -> ["intake", "urgent"]
#
# Calling it without `tags` must return a brand-new list each time.
# Calling it with `tags` must NOT change the caller's list: return a new one.
# Today: the second no-argument call returns ["intake", "followup"] (state
# leaks between calls), and the caller's list gets modified.
def add_tag(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag)
    return tags


# ── Q2 · format_name ─────────────────────────────────────────── fix the bug ──
# Format a patient's display name. `middle` is shown as its first letter plus
# a period. With `last_first=True` the format is "Last, First M.".
#
#   format_name("Ada", "King")                                    -> "Ada King"
#   format_name("Ada", "King", middle="Byron")                    -> "Ada B. King"
#   format_name("Ada", "King", last_first=True)                   -> "King, Ada"
#   format_name("Ada", "King", middle="Byron", last_first=True)   -> "King, Ada B."
#   format_name("Ada", "King", "Byron")                           -> raises TypeError
#
# `middle` and `last_first` must be KEYWORD-ONLY: passing them positionally
# raises TypeError (Python does this for you once the signature is right).
# Keep the parameter names and defaults.
# Today: always returns "First Last", ignoring `middle` and `last_first`, and
# accepts `middle` positionally.
def format_name(first: str, last: str, middle: str | None = None, last_first: bool = False) -> str:
    return first + " " + last


# ── Q3 · total_cents ───────────────────────────────────────────── implement ──
# Sum any number of line-item amounts (in cents), then apply `discount_pct`
# percent off the total. Return the result rounded to the nearest whole cent
# as an int (use round()).
#
#   total_cents(1000, 2500)                    -> 3500
#   total_cents()                              -> 0      no amounts at all
#   total_cents(1000, 2500, discount_pct=10)   -> 3150   3500 minus 10%
#   total_cents(999, discount_pct=33)          -> 669    669.33 rounds to 669
#
# TS equivalent: `function totalCents(...amounts: number[]) { ... }`
def total_cents(*amounts: int, discount_pct: float = 0) -> int:
    raise NotImplementedError


# ── Q4 · build_query ───────────────────────────────────────────── implement ──
# Build an API URL from a path plus any number of keyword arguments.
# Each keyword becomes `key=value`, joined with "&", in the order the
# arguments were passed. Skip arguments whose value is None. If nothing is
# left, return the bare path with no "?".
#
#   build_query("/patients", page=2, payer="Aetna", q=None)
#       -> "/patients?page=2&payer=Aetna"   q=None is skipped
#   build_query("/patients")             -> "/patients"
#   build_query("/patients", q=None)     -> "/patients"     no trailing "?"
#
# No URL-encoding needed.
def build_query(path: str, **params: str | int | None) -> str:
    raise NotImplementedError
