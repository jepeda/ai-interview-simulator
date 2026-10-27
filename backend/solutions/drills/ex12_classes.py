"""Drill 12 - Classes (reference solution)."""

from datetime import date
from decimal import Decimal


class Money:
    def __init__(self, cents: int) -> None:
        if not isinstance(cents, int) or isinstance(cents, bool):
            raise TypeError(f"cents must be an int, got {type(cents).__name__}")
        self.cents = cents

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.cents + other.cents)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.cents == other.cents

    def __hash__(self) -> int:
        return hash(self.cents)

    def __repr__(self) -> str:
        return f"Money({self.cents})"

    def __str__(self) -> str:
        return f"${self.cents / 100:,.2f}"

    @classmethod
    def from_dollars(cls, dollars: str | int) -> "Money":
        return cls(int(Decimal(str(dollars)) * 100))


class Patient:
    def __init__(self, first_name: str, last_name: str, date_of_birth: date) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def age_on(self, on: date) -> int:
        had_birthday = (on.month, on.day) >= (self.date_of_birth.month, self.date_of_birth.day)
        return on.year - self.date_of_birth.year - (0 if had_birthday else 1)
