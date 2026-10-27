"""Drill 01 - Dictionaries (reference solution)."""


def get_copay_cents(plan: dict) -> int:
    return plan.get("copay_cents", 0)


def count_by_status(appointments: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for appt in appointments:
        counts[appt["status"]] = counts.get(appt["status"], 0) + 1
    return counts


def merge_preferences(defaults: dict, overrides: dict) -> dict:
    return {**defaults, **overrides}  # or: defaults | overrides


def invert_index(patient_ids_by_provider: dict[str, list[int]]) -> dict[int, str]:
    result: dict[int, str] = {}
    for provider, patient_ids in patient_ids_by_provider.items():
        for patient_id in patient_ids:
            result[patient_id] = provider
    return result
