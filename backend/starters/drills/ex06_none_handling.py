"""Drill 06 - None handling and truthiness.

TS mental model:
  null / undefined           -> None
  x ?? fallback              -> x if x is not None else fallback   (NOT `x or fallback`!)
  a?.b?.c                    -> no operator; use .get() chains or explicit checks
  x === null                 -> x is None

Falsy values in Python: None, False, 0, 0.0, "", [], {}, set()
(Unlike JS, an EMPTY LIST and EMPTY DICT are falsy.)

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen None/truthiness cheat sheet.
"""


# ── Q1 · display_copay ───────────────────────────────────────── fix the bug ──
# The checkout screen shows the patient's copay. `copay_cents` is None when
# the plan hasn't been verified yet; 0 means a genuine $0 copay.
# Return "Unknown" for None, otherwise dollars with a "$", thousands
# separators, and exactly 2 decimal places.
#
#   display_copay(None)     -> "Unknown"
#   display_copay(0)        -> "$0.00"       0 is a real copay, not unknown
#   display_copay(5)        -> "$0.05"
#   display_copay(2500)     -> "$25.00"
#   display_copay(123456)   -> "$1,234.56"
#
# Today: 0 shows "Unknown", 2500 shows "$25.0", 123456 shows "$1234.56".
def display_copay(copay_cents: int | None) -> str:
    if not copay_cents:
        return "Unknown"
    return "$" + str(copay_cents / 100)


# ── Q2 · primary_phone ───────────────────────────────────────── fix the bug ──
# Patient records from the legacy EHR are inconsistent. Return
# patient["contact"]["phones"][0]["number"] - the FIRST phone's number - or
# None if anything along the way is unavailable:
#   "contact" missing or None, "phones" missing or None or [], or the first
#   phone dict has no "number".
#
#   primary_phone({"contact": {"phones": [{"number": "555-0100"},
#                                         {"number": "555-0199"}]}})  -> "555-0100"
#   primary_phone({})                                   -> None
#   primary_phone({"contact": None})                    -> None
#   primary_phone({"contact": {}})                      -> None
#   primary_phone({"contact": {"phones": None}})        -> None
#   primary_phone({"contact": {"phones": []}})          -> None
#   primary_phone({"contact": {"phones": [{}]}})        -> None
#
# Never raise. Don't use try/except.
# Today: raises KeyError / TypeError / IndexError on every case except the
# happy path.
# TS equivalent: `patient.contact?.phones?.[0]?.number ?? null`
def primary_phone(patient: dict) -> str | None:
    return patient["contact"]["phones"][0]["number"]


# ── Q3 · first_present ───────────────────────────────────────── fix the bug ──
# Pick the first available value from a list of fallbacks (e.g. preferred
# name, legal name, ...). Return the first argument that is not None.
# An empty string "" is a real value and counts as present.
# Return None if every argument is None, or if there are no arguments.
#
#   first_present(None, "a", "b")   -> "a"
#   first_present(None, "", "x")    -> ""      "" is present
#   first_present(None, None)       -> None
#   first_present()                 -> None
#
# Today: skips "" and returns "x" in the second example.
# TS equivalent: `values.find(v => v !== null) ?? null`
def first_present(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value


# ── Q4 · member_id_or_self_pay ─────────────────────────────────── implement ──
# Claims need the patient's insurance member id. Return patient["member_id"]
# with surrounding whitespace stripped. If the key is missing, the value is
# None, or it is empty/whitespace-only, return the string "SELF-PAY".
#
#   member_id_or_self_pay({"member_id": " W123 "})   -> "W123"
#   member_id_or_self_pay({"member_id": None})       -> "SELF-PAY"
#   member_id_or_self_pay({"member_id": "   "})      -> "SELF-PAY"   blank after strip
#   member_id_or_self_pay({})                        -> "SELF-PAY"
def member_id_or_self_pay(patient: dict) -> str:
    raise NotImplementedError
