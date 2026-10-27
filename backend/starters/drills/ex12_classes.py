"""Drill 12 - Classes.

TS mental model:
  constructor(...)            -> def __init__(self, ...)       (self is explicit, ALWAYS first param)
  get fullName() { }          -> @property  def full_name(self)
  static fromDollars() { }    -> @classmethod def from_dollars(cls, ...)   (cls = the class)
  toString()                  -> __str__   (for users)   /  __repr__ (for developers/debugging)
  a.equals(b)                 -> __eq__    (== calls it; default compares identity like ===)
  a.plus(b)                   -> __add__   (enables a + b)
  private x                   -> _x by convention (nothing is truly private)

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen classes cheat sheet.
"""

from datetime import date


# ── Q1 · Money ───────────────────────────────────────────────── fix the bug ──
# A value object for an amount of money, stored as integer cents (never floats:
# billing totals must be exact). Every behaviour below is tested:
#
#   Money(2500) + Money(150)          -> Money(2650)   a Money, with .cents == 2650
#   Money(100) == Money(100)          -> True          equal by value, not identity
#   Money(100) != Money(101)          -> True
#   repr(Money(2650))                 -> "Money(2650)"
#   str(Money(123456))                -> "$1,234.56"   thousands commas, 2 decimals
#   str(Money(5))                     -> "$0.05"
#   Money(19.99)                      -> raises TypeError    cents must be an int
#   Money("100")                      -> raises TypeError
#   Money.from_dollars("19.99")       -> Money(1999)
#   Money.from_dollars("0.29")        -> Money(29)     exact: not 28
#   Money.from_dollars("1")           -> Money(100)    an instance of Money
#
# from_dollars must be a classmethod (an alternate constructor on the class).
# Comparing a Money to a non-Money should not crash.
#
# Today: `+` returns a bare int, == is False for equal amounts, repr is
# "<...Money object at 0x...>", str gives "2650", floats are accepted, and
# from_dollars("0.29") produces 28.999999999999996 cents.
class Money:
    # Validate: `cents` must be an int (bool doesn't count as money either).
    def __init__(self, cents):
        self.cents = cents

    # Money + Money -> a new Money.
    def __add__(self, other):
        return self.cents + other.cents

    # Human-facing text: "$1,234.56".
    def __str__(self):
        return str(self.cents)

    # Parse a dollar string like "19.99" into exact cents.
    def from_dollars(dollars):
        return Money(float(dollars) * 100)


# ── Q2 · Patient ─────────────────────────────────────────────── fix the bug ──
# A patient record from intake.
#
# full_name: read as an attribute, no parentheses. "<first> <last>".
#   p = Patient("Ada", "King", date(1990, 12, 10))
#   p.full_name                   -> "Ada King"
#
# age_on(on): whole years old on the date `on`. The age only goes up ON the
# birthday, not at the start of the year.
#   p.age_on(date(2026, 12, 9))   -> 35     day before the birthday
#   p.age_on(date(2026, 12, 10))  -> 36     the birthday itself counts
#   p.age_on(date(2027, 1, 1))    -> 36     new year, birthday not yet reached
#
# Today: p.full_name hands back a method object instead of "Ada King" (and
# calling it raises TypeError), and age_on is one year too old before the
# birthday.
# TS equivalent: `get fullName() { return this.firstName + " " + this.lastName }`
class Patient:
    def __init__(self, first_name: str, last_name: str, date_of_birth: date) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth

    def full_name():
        return f"{self.first_name} {self.last_name}"

    def age_on(self, on: date) -> int:
        return on.year - self.date_of_birth.year
