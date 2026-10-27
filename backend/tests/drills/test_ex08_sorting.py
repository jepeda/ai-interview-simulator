from datetime import date, datetime

from drills.ex08_sorting import by_termination_date, newest_first, rank_providers, sort_by_name


def test_sort_by_name_case_insensitive_with_tiebreak():
    patients = [
        {"first_name": "zoe", "last_name": "smith"},
        {"first_name": "Al", "last_name": "Smith"},
        {"first_name": "Bea", "last_name": "adams"},
    ]
    result = sort_by_name(patients)
    assert [(p["first_name"], p["last_name"]) for p in result] == [
        ("Bea", "adams"),
        ("Al", "Smith"),
        ("zoe", "smith"),
    ]


def test_sort_by_name_does_not_mutate():
    patients = [{"first_name": "B", "last_name": "B"}, {"first_name": "A", "last_name": "A"}]
    original = list(patients)
    sort_by_name(patients)
    assert patients == original


def test_newest_first():
    notes = [
        {"id": 1, "created_at": datetime(2026, 1, 5, 9, 0)},
        {"id": 2, "created_at": datetime(2026, 3, 1, 8, 0)},
        {"id": 3, "created_at": datetime(2025, 12, 31, 23, 59)},
    ]
    assert [n["id"] for n in newest_first(notes)] == [2, 1, 3]


def test_by_termination_date_none_last():
    plans = [
        {"id": "open", "termination_date": None},
        {"id": "late", "termination_date": date(2027, 1, 1)},
        {"id": "early", "termination_date": date(2026, 6, 30)},
        {"id": "open2", "termination_date": None},
    ]
    assert [p["id"] for p in by_termination_date(plans)] == ["early", "late", "open", "open2"]


def test_rank_providers():
    providers = [
        {"name": "Ng", "rating": 4.5},
        {"name": "Lee", "rating": 4.9},
        {"name": "Diaz", "rating": 4.5},
        {"name": "Ames", "rating": 3.0},
    ]
    assert rank_providers(providers) == ["Lee", "Diaz", "Ng", "Ames"]
