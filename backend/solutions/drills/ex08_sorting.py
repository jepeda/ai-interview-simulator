"""Drill 08 - Sorting (reference solution)."""

from datetime import date


def sort_by_name(patients: list[dict]) -> list[dict]:
    return sorted(patients, key=lambda p: (p["last_name"].lower(), p["first_name"].lower()))


def newest_first(notes: list[dict]) -> list[dict]:
    return sorted(notes, key=lambda n: n["created_at"], reverse=True)


def by_termination_date(plans: list[dict]) -> list[dict]:
    return sorted(
        plans,
        key=lambda p: (p["termination_date"] is None, p["termination_date"] or date.min),
    )


def rank_providers(providers: list[dict]) -> list[str]:
    ranked = sorted(providers, key=lambda p: (-p["rating"], p["name"]))
    return [p["name"] for p in ranked]
