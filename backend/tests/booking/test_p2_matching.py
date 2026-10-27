"""Part 2: provider search (services/matching.py)."""

from datetime import date

import pytest

from booking.services.matching import SearchCriteria, search_providers

TODAY = date(2026, 10, 26)  # the frozen clock's date (see conftest)
FAR_FUTURE = date(2027, 12, 31)


@pytest.fixture
def roster(make_provider):
    make_provider("Ada", "Lee", rating=4.9, payers=["Aetna", "Cigna"], specialties=["anxiety", "depression"])
    make_provider("Ben", "Ng", rating=4.9, licenses={"NY": FAR_FUTURE, "NJ": FAR_FUTURE})
    make_provider("Cara", "Diaz", rating=5.0, licenses={"NY": date(2026, 10, 25)})  # expired yesterday
    make_provider("Dan", "Moss", rating=4.0, accepting=False)
    make_provider("Eve", "Park", rating=4.8, licenses={"CA": FAR_FUTURE})
    make_provider("Fay", "Quinn", rating=None, payers=["UnitedHealthcare"], specialties=["trauma"])
    make_provider("Gil", "Ross", rating=3.0, licenses={"NY": TODAY}, payers=["Cigna"], specialties=["depression"])


def search(db, **kwargs) -> tuple[list[str], int]:
    providers, total = search_providers(db, SearchCriteria(**kwargs), TODAY)
    return [f"{p.first_name} {p.last_name}" for p in providers], total


def test_state_filter_with_license_expiry_and_ordering(db, roster):
    names, total = search(db, state="NY")
    # rating desc, ties by last name, unrated last; Cara's license expired; Gil's expires today (valid)
    assert names == ["Ada Lee", "Ben Ng", "Gil Ross", "Fay Quinn"]
    assert total == 4


def test_each_provider_appears_once(db, roster):
    names, total = search(db, state="NJ")
    assert names == ["Ben Ng"]
    assert total == 1
    names, _ = search(db, state="NY", page_size=50)
    assert len(names) == len(set(names))


def test_payer_filter_is_case_insensitive(db, roster):
    names, total = search(db, state="NY", payer="aetna")
    assert names == ["Ada Lee", "Ben Ng"]
    assert total == 2


def test_specialty_filter(db, roster):
    names, _ = search(db, state="NY", specialty="depression")
    assert names == ["Ada Lee", "Gil Ross"]


def test_can_include_providers_not_accepting_new_patients(db, roster):
    names, total = search(db, state="NY", accepting_new_patients_only=False)
    assert names == ["Ada Lee", "Ben Ng", "Dan Moss", "Gil Ross", "Fay Quinn"]
    assert total == 5


def test_pagination(db, roster):
    page1, total1 = search(db, state="NY", page=1, page_size=3)
    page2, total2 = search(db, state="NY", page=2, page_size=3)
    assert page1 == ["Ada Lee", "Ben Ng", "Gil Ross"]
    assert page2 == ["Fay Quinn"]
    assert total1 == total2 == 4


def test_no_matches(db, roster):
    assert search(db, state="TX") == ([], 0)


def test_search_endpoint(client, roster):
    response = client.get(
        "/providers/search", params={"state": "ny", "payer": "AETNA", "specialty": "Anxiety"}
    )
    assert response.status_code == 200
    body = response.json()
    assert [f"{p['first_name']} {p['last_name']}" for p in body["items"]] == ["Ada Lee", "Ben Ng"]
    assert body["total"] == 2
    assert body["items"][1]["states"] == ["NJ", "NY"]


def test_search_endpoint_validates_state(client):
    assert client.get("/providers/search", params={"state": "New York"}).status_code == 422
