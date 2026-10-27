"""Drill 11 - Custom exception hierarchies and context managers.

TS mental model: `class EligibilityError extends ClinicError` becomes
`class EligibilityError(ClinicError)`, and `super(msg)` becomes `super().__init__(msg)`.
`with x as y:` is try/finally around a block (like TS 5.2 `using`): setup runs
before the block, cleanup ALWAYS runs after it, even if the block raises.
@contextmanager turns a generator into a context manager: code before the
`yield` is setup, the `with` body runs at the `yield`, code after it is cleanup.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen context-manager cheat sheet.
"""

from contextlib import contextmanager


# ClinicError is provided: the base class every clinic domain error inherits from,
# so callers can catch the whole family with one `except ClinicError`.
class ClinicError(Exception):
    ...


# ── Q1 · EligibilityError ──────────────────────────────────────── implement ──
# The eligibility service raises this when a patient's coverage can't be used.
# Make it a real exception in the ClinicError family (today it isn't even an
# Exception, so it can't be raised).
#
# Constructor: EligibilityError(patient_id: int, reason: str), positional or keyword.
#   err = EligibilityError(patient_id=7, reason="plan terminated")
#   err.patient_id                -> 7
#   err.reason                    -> "plan terminated"
#   str(err)                      -> "Patient 7 is not eligible: plan terminated"
#   isinstance(err, ClinicError)  -> True     and therefore also an Exception
#
# TS equivalent: `class EligibilityError extends ClinicError { constructor(...) { super(...) } }`
class EligibilityError:
    ...


# ── Q2 · require_eligible ──────────────────────────────────────── implement ──
# Guard called before booking. `patient` is a dict with "id", "eligible" and
# "reason" keys. If patient["eligible"] is falsy, raise
# EligibilityError(patient["id"], patient["reason"]); otherwise do nothing.
#
#   require_eligible({"id": 1, "eligible": True, "reason": ""})   -> None
#   require_eligible({"id": 3, "eligible": False, "reason": "no coverage"})
#       -> raises EligibilityError; `except ClinicError as e` catches it, e.patient_id == 3
def require_eligible(patient: dict) -> None:
    raise NotImplementedError


# ── Q3 · audit ───────────────────────────────────────────────── fix the bug ──
# Wrap a billing action so its lifecycle lands in an audit trail:
#
#   with audit(events, "bill"):
#       events.append("work")
#   events  -> ["start:bill", "work", "ok:bill"]
#
# - on entry, append f"start:{action}"
# - if the block finishes normally, append f"ok:{action}"
# - if the block raises, append f"error:{action}" (and NOT "ok:..."), then let
#   the SAME exception keep propagating to the caller: the audit never hides errors
#
#   with audit(events, "bill"): raise RuntimeError("boom")
#       -> RuntimeError reaches the caller; events == ["start:bill", "error:bill"]
#
# Today: a failing block records only "start:bill"; the error is never logged.
@contextmanager
def audit(events: list[str], action: str):
    events.append(f"start:{action}")
    yield
    events.append(f"ok:{action}")


# ── Q4 · StagedChanges ───────────────────────────────────────── fix the bug ──
# Bulk-import rows all-or-nothing. Rows the caller adds inside the block are
# held aside and only copied onto `target` when the block exits cleanly.
#
#   target = ["existing"]
#   with StagedChanges(target) as staged:
#       staged.append("a")
#       staged.append("b")
#       # target is still ["existing"] here: nothing applied mid-block
#   target  -> ["existing", "a", "b"]     appended in the order they were staged
#
# If the block raises (e.g. ValueError("bad row")), `target` stays exactly as it
# was and the exception propagates to the caller.
#
# Today: rows go straight into `target` mid-block, and any exception raised in
# the block silently disappears.
class StagedChanges:
    def __init__(self, target: list[str]) -> None:
        self.target = target
        self.staged: list[str] = []

    def __enter__(self) -> list[str]:
        return self.target

    def __exit__(self, exc_type, exc, tb) -> bool:
        return True
