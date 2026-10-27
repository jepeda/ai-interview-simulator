"""Drill 04 - collections (reference solution)."""

from collections import Counter, defaultdict


def group_by_provider(appointments: list[dict]) -> dict[str, list[int]]:
    groups: defaultdict[str, list[int]] = defaultdict(list)
    for appt in appointments:
        groups[appt["provider"]].append(appt["id"])
    return dict(groups)


def top_diagnoses(codes: list[str], n: int) -> list[tuple[str, int]]:
    return Counter(codes).most_common(n)


def missing_fields(record: dict, required: set[str]) -> set[str]:
    return {name for name in required if record.get(name) is None}


def shared_patients(provider_a: list[int], provider_b: list[int]) -> list[int]:
    return sorted(set(provider_a) & set(provider_b))
