import pytest

from drills.ex02_lists_tuples import chunk, first_and_last, numbered, pair_up, split_head_tail


def test_first_and_last():
    assert first_and_last(["a", "b", "c"]) == ("a", "c")


def test_first_and_last_single():
    assert first_and_last(["solo"]) == ("solo", "solo")


def test_first_and_last_empty():
    assert first_and_last([]) is None


def test_chunk_uneven():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_chunk_even_and_empty():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
    assert chunk([], 3) == []


def test_numbered_default_start():
    assert numbered(["Ann", "Bo"]) == ["1. Ann", "2. Bo"]


def test_numbered_custom_start():
    assert numbered(["Ann", "Bo"], start=10) == ["10. Ann", "11. Bo"]


def test_pair_up_order_is_id_then_name():
    assert pair_up(["Ann", "Bo"], [7, 9]) == [(7, "Ann"), (9, "Bo")]


def test_pair_up_length_mismatch_raises():
    with pytest.raises(ValueError):
        pair_up(["Ann", "Bo"], [7])


def test_split_head_tail():
    assert split_head_tail([1, 2, 3]) == (1, [2, 3])
    assert split_head_tail([4]) == (4, [])


def test_split_head_tail_empty_raises():
    with pytest.raises(ValueError):
        split_head_tail([])
