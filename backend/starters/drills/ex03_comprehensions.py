"""Drill 03 - Comprehensions.

TS mental model:
  items.filter(p => p.active).map(p => p.email)
    -> [p["email"] for p in items if p["active"]]
  Object.fromEntries(items.map(p => [p.id, p]))
    -> {p["id"]: p for p in items}
  new Set(items.map(p => p.payer))
    -> {p["payer"] for p in items}
  items.flatMap(v => v.codes)
    -> [code for v in items for code in v["codes"]]     (loops read left-to-right)

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen comprehensions cheat sheet.
"""


# ── Q1 · active_emails ───────────────────────────────────────── fix the bug ──
# Build the mailing list for a clinic newsletter. Each patient is a dict with
# a "status" ("active", "archived", ...) and an "email" (a str, or None).
#
# Return the emails of patients whose status is exactly "active", with
# surrounding whitespace stripped and lowercased. Skip patients whose email
# is None. Keep input order.
#
#   active_emails([{"status": "active",   "email": " Ann@X.com "},
#                  {"status": "archived", "email": "b@x.com"},
#                  {"status": "active",   "email": "CARL@x.com"}])
#       -> ["ann@x.com", "carl@x.com"]
#   active_emails([{"status": "active", "email": None},
#                  {"status": "active", "email": "d@x.com"}])
#       -> ["d@x.com"]                     a None email is skipped, not an error
#
# Write it as a single `return` of a list comprehension.
# Today: returns every patient's email, unfiltered and un-normalized.
def active_emails(patients: list[dict]) -> list[str]:
    return [p["email"] for p in patients]


# ── Q2 · index_by_id ───────────────────────────────────────────── implement ──
# The patient page looks patients up by id. Build {patient["id"]: patient}.
# The values are the original patient dicts (not copies).
#
#   index_by_id([{"id": 1, "name": "Ann"}, {"id": 2, "name": "Bo"}])
#       -> {1: {"id": 1, "name": "Ann"}, 2: {"id": 2, "name": "Bo"}}
#   index_by_id([])   -> {}
#
# Write it as a single `return` of a dict comprehension.
# TS equivalent: `Object.fromEntries(patients.map(p => [p.id, p]))`
def index_by_id(patients: list[dict]) -> dict[int, dict]:
    raise NotImplementedError


# ── Q3 · unique_payers ─────────────────────────────────────────── implement ──
# The billing filter dropdown lists every insurance payer once. Each plan is a
# dict with a "payer" key. Return the distinct payers, sorted alphabetically.
#
#   unique_payers([{"payer": "Cigna"}, {"payer": "Aetna"}, {"payer": "Cigna"}])
#       -> ["Aetna", "Cigna"]
#
# The result must be a list (not a set). Use a set comprehension to dedupe.
# TS equivalent: `[...new Set(plans.map(p => p.payer))].sort()`
def unique_payers(plans: list[dict]) -> list[str]:
    raise NotImplementedError


# ── Q4 · flatten_diagnoses ─────────────────────────────────────── implement ──
# Each visit has a "codes" list of ICD-10 diagnosis codes (possibly empty).
# Return every code from every visit as one flat list: visits in input order,
# codes in their order within each visit, duplicates kept.
#
#   flatten_diagnoses([{"codes": ["F41.1", "F32.0"]},
#                      {"codes": []},
#                      {"codes": ["F41.1"]}])   -> ["F41.1", "F32.0", "F41.1"]
#
# Write it as a single `return` of a nested list comprehension.
# TS equivalent: `visits.flatMap(v => v.codes)`
def flatten_diagnoses(visits: list[dict]) -> list[str]:
    raise NotImplementedError
