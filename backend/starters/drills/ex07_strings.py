"""Drill 07 - Strings and f-strings.

TS mental model: f"{a} {b}" is a template literal `${a} ${b}`, and the part after
a colon inside the braces (a "format spec") does the job of toFixed/padStart/
toLocaleString. Strings are immutable: every method returns a NEW string.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen string cheat sheet.
"""


# ── Q1 · format_member_id ────────────────────────────────────── fix the bug ──
# Members type their insurance member id into the intake form however they
# like: lowercase, stray spaces, dashes in random places. Normalize it.
#
# Steps: trim surrounding whitespace, uppercase, remove every space and "-",
# then cut the result into chunks of 3 characters (left to right) joined by
# "-". The last chunk may be shorter than 3.
#
#   format_member_id(" ab1 23-4567 ")   -> "AB1-234-567"
#   format_member_id("w12345")          -> "W12-345"
#   format_member_id("abcd")            -> "ABC-D"    short last chunk
#   format_member_id("x")               -> "X"        one chunk, no dash
#
# Never a leading or trailing "-".
# Today: only uppercases, so " ab1 23-4567 " -> " AB1 23-4567 ".
def format_member_id(raw: str) -> str:
    return raw.upper()


# ── Q2 · initials ──────────────────────────────────────────────── implement ──
# The provider directory shows a patient's initials instead of their name.
# Return the first letter of each word, uppercased, each followed by ".".
#
#   initials("mary  ann o'neil")   -> "M.A.O."   double space is not a word
#   initials("  Ada ")             -> "A."       leading/trailing spaces ignored
#
# Words are separated by any amount of whitespace; empty "words" never
# produce a letter or a stray ".".
# TS equivalent: name.trim().split(/\s+/).map(w => w[0].toUpperCase() + ".").join("")
def initials(full_name: str) -> str:
    raise NotImplementedError


# ── Q3 · format_money ────────────────────────────────────────── fix the bug ──
# Billing stores money as integer cents. Render it for an invoice: "$",
# thousands separators, and always exactly 2 decimal places.
#
#   format_money(123456)      -> "$1,234.56"
#   format_money(5)           -> "$0.05"
#   format_money(0)           -> "$0.00"
#   format_money(100000000)   -> "$1,000,000.00"
#   format_money(-1250)       -> "-$12.50"     sign goes BEFORE the "$"
#
# "$-12.50" is wrong; so is "$12.5".
# Today: format_money(123456) -> "$1234.56" and format_money(0) -> "$0.0".
# TS equivalent: Intl.NumberFormat("en-US", {style: "currency", currency: "USD"})
def format_money(cents: int) -> str:
    return f"${cents / 100}"


# ── Q4 · mrn ───────────────────────────────────────────────────── implement ──
# Medical record numbers are printed on wristbands as "MRN-" followed by the
# number left-padded with zeros to at least 6 digits.
#
#   mrn(42)        -> "MRN-000042"
#   mrn(1234567)   -> "MRN-1234567"   longer than 6 digits: never truncated
#
# TS equivalent: `MRN-${String(n).padStart(6, "0")}`
def mrn(n: int) -> str:
    raise NotImplementedError
