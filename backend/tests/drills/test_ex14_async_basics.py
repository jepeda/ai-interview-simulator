import asyncio
import inspect

from drills.ex14_async_basics import (
    FakeEligibilityAPI,
    check_many,
    check_many_sync,
    is_eligible,
)


def test_is_eligible_is_async_and_awaits_the_api():
    assert inspect.iscoroutinefunction(is_eligible)
    api = FakeEligibilityAPI()
    assert asyncio.run(is_eligible(api, 2)) is True
    assert asyncio.run(is_eligible(api, 3)) is False


def test_check_many_results():
    api = FakeEligibilityAPI()
    result = asyncio.run(check_many(api, [1, 2, 3, 4]))
    assert result == {1: False, 2: True, 3: False, 4: True}


def test_check_many_runs_concurrently():
    api = FakeEligibilityAPI()
    asyncio.run(check_many(api, [1, 2, 3, 4, 5]))
    assert api.max_in_flight == 5, "all fetches should be in flight at the same time"


def test_check_many_empty():
    assert asyncio.run(check_many(FakeEligibilityAPI(), [])) == {}


def test_check_many_sync():
    assert check_many_sync([10, 11]) == {10: True, 11: False}
