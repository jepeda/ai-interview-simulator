"""Drill 10 - Exceptions.

TS mental model:
  try { } catch (e) { } finally { }    -> try: ... except SomeError as e: ... finally: ...
  throw new Error("x")                 -> raise ValueError("x")
  new Error("x", { cause: err })       -> raise NewError("x") from err     (sets __cause__)
Catch SPECIFIC exception types; a bare `except:` or `except Exception:` hides bugs.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen exceptions cheat sheet.
"""

from decimal import Decimal, InvalidOperation  # noqa: F401


# Domain error used by Q3. Already complete: nothing to change here.
class PatientNotFoundError(Exception):
    """Raised when a patient id does not exist."""


# ── Q1 · parse_copay ─────────────────────────────────────────── fix the bug ──
# Front-desk staff type copay amounts into a free-text box. Parse the string
# into integer cents, strictly: money must never be silently mangled.
#
# Accept: surrounding whitespace, an optional leading "$", "," thousands
# separators, and 0, 1 or 2 decimal places.
#
#   parse_copay("$25")           -> 2500
#   parse_copay("25.00")         -> 2500
#   parse_copay(" $1,250.50 ")   -> 125050
#   parse_copay("0.07")          -> 7       exact: no float rounding errors
#   parse_copay("$0")            -> 0
#
# Reject with ValueError, and the message must contain the original input:
#   ""  "   "  "$"      blank / nothing after the "$"
#   "abc"               not a number (message must contain "abc")
#   "-5"                negative
#   "12.345"            more than 2 decimal places
#
# Only ValueError may escape: no other exception type, whatever the input.
# Today: valid input like "$25" raises ValueError, while "-5" and "12.345"
# are silently accepted.
def parse_copay(raw: str) -> int:
    return int(float(raw) * 100)


# ── Q2 · safe_parse_copay ──────────────────────────────────────── implement ──
# Same rules as parse_copay, for callers that just want "no value" on bad
# input: return the cents, or None instead of raising ValueError.
#
#   safe_parse_copay("$10")    -> 1000
#   safe_parse_copay("nope")   -> None
#
# Reuse parse_copay rather than duplicating its rules.
def safe_parse_copay(raw: str) -> int | None:
    raise NotImplementedError


# ── Q3 · load_patient ────────────────────────────────────────── fix the bug ──
# `store` maps patient id -> patient record. Return store[patient_id].
# A missing id should surface as our domain error, not a raw KeyError.
#
#   load_patient({1: {"id": 1}}, 1)   -> {"id": 1}
#   load_patient({}, 42)              -> raises PatientNotFoundError, message contains "42"
#
# The new error must be CHAINED from the original KeyError, so that
# err.__cause__ is that KeyError (debuggers then show both tracebacks).
# Today: a missing id raises a bare KeyError.
# TS equivalent: throw new PatientNotFoundError(`Patient ${id} not found`, { cause: err })
def load_patient(store: dict[int, dict], patient_id: int) -> dict:
    return store[patient_id]


# ── Q4 · parse_batch ───────────────────────────────────────────── implement ──
# A CSV import gives us a column of raw copay strings. Parse each with
# parse_copay. Return a tuple (parsed_cents, error_messages):
#   parsed_cents   - the cents of every good value, in input order
#   error_messages - one string per bad value, in input order: the message
#                    of the ValueError that parse_copay raised
#
#   parse_batch(["$10", "bad", "2.50", ""])
#       -> ([1000, 250], [<message containing "bad">, <message about "">])
#   parse_batch([])   -> ([], [])
#
# One bad value must not stop the batch: keep going to the end.
def parse_batch(raws: list[str]) -> tuple[list[int], list[str]]:
    raise NotImplementedError
