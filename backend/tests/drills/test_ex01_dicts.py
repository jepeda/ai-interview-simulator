from drills.ex01_dicts import count_by_status, get_copay_cents, invert_index, merge_preferences


def test_get_copay_present():
    assert get_copay_cents({"copay_cents": 2500}) == 2500


def test_get_copay_missing_defaults_to_zero():
    assert get_copay_cents({}) == 0


def test_get_copay_zero_is_kept():
    assert get_copay_cents({"copay_cents": 0}) == 0


def test_count_by_status():
    appts = [{"status": "scheduled"}, {"status": "cancelled"}, {"status": "scheduled"}]
    assert count_by_status(appts) == {"scheduled": 2, "cancelled": 1}


def test_count_by_status_empty():
    assert count_by_status([]) == {}


def test_merge_preferences_overrides_win():
    merged = merge_preferences({"theme": "light", "tz": "UTC"}, {"theme": "dark"})
    assert merged == {"theme": "dark", "tz": "UTC"}


def test_merge_preferences_does_not_mutate_inputs():
    defaults = {"theme": "light"}
    overrides = {"theme": "dark", "lang": "en"}
    merge_preferences(defaults, overrides)
    assert defaults == {"theme": "light"}
    assert overrides == {"theme": "dark", "lang": "en"}


def test_invert_index():
    result = invert_index({"Dr. Lee": [1, 2], "Dr. Ng": [3]})
    assert result == {1: "Dr. Lee", 2: "Dr. Lee", 3: "Dr. Ng"}


def test_invert_index_empty_lists():
    assert invert_index({"Dr. Lee": []}) == {}
