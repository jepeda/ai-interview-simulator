from drills.ex03_comprehensions import active_emails, flatten_diagnoses, index_by_id, unique_payers


def test_active_emails_filters_and_normalizes():
    patients = [
        {"status": "active", "email": " Ann@X.com "},
        {"status": "archived", "email": "b@x.com"},
        {"status": "active", "email": "CARL@x.com"},
    ]
    assert active_emails(patients) == ["ann@x.com", "carl@x.com"]


def test_active_emails_skips_none():
    patients = [{"status": "active", "email": None}, {"status": "active", "email": "d@x.com"}]
    assert active_emails(patients) == ["d@x.com"]


def test_index_by_id():
    a, b = {"id": 1, "name": "Ann"}, {"id": 2, "name": "Bo"}
    assert index_by_id([a, b]) == {1: a, 2: b}
    assert index_by_id([]) == {}


def test_unique_payers_sorted_and_distinct():
    plans = [{"payer": "Cigna"}, {"payer": "Aetna"}, {"payer": "Cigna"}]
    assert unique_payers(plans) == ["Aetna", "Cigna"]


def test_unique_payers_returns_list():
    assert isinstance(unique_payers([{"payer": "Aetna"}]), list)


def test_flatten_diagnoses():
    visits = [{"codes": ["F41.1", "F32.0"]}, {"codes": []}, {"codes": ["F41.1"]}]
    assert flatten_diagnoses(visits) == ["F41.1", "F32.0", "F41.1"]
