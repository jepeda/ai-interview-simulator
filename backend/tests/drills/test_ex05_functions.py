import pytest

from drills.ex05_functions import add_tag, build_query, format_name, total_cents


def test_add_tag_default_list_is_not_shared():
    assert add_tag("intake") == ["intake"]
    assert add_tag("followup") == ["followup"]


def test_add_tag_does_not_mutate_argument():
    existing = ["intake"]
    result = add_tag("urgent", existing)
    assert result == ["intake", "urgent"]
    assert existing == ["intake"]


def test_format_name_basic():
    assert format_name("Ada", "King") == "Ada King"


def test_format_name_middle_initial():
    assert format_name("Ada", "King", middle="Byron") == "Ada B. King"


def test_format_name_last_first():
    assert format_name("Ada", "King", last_first=True) == "King, Ada"
    assert format_name("Ada", "King", middle="Byron", last_first=True) == "King, Ada B."


def test_format_name_keyword_only():
    with pytest.raises(TypeError):
        format_name("Ada", "King", "Byron")  # type: ignore[misc]


def test_total_cents():
    assert total_cents(1000, 2500) == 3500
    assert total_cents() == 0


def test_total_cents_discount():
    assert total_cents(1000, 2500, discount_pct=10) == 3150
    assert total_cents(999, discount_pct=33) == 669


def test_build_query():
    assert build_query("/patients", page=2, payer="Aetna", q=None) == "/patients?page=2&payer=Aetna"


def test_build_query_no_params():
    assert build_query("/patients") == "/patients"
    assert build_query("/patients", q=None) == "/patients"
