import asyncio
import time

from drills.ex15_async_patterns import (
    FlakyPayerAPI,
    fetch_all_settled,
    fetch_limited,
    fetch_with_timeout,
)


def test_fetch_with_timeout_fast():
    api = FlakyPayerAPI()
    assert asyncio.run(fetch_with_timeout(api, 1, seconds=0.5)) == {"patient_id": 1, "plan": "PPO"}


def test_fetch_with_timeout_slow_returns_none_quickly():
    api = FlakyPayerAPI(slow_ids={1})
    started = time.perf_counter()
    assert asyncio.run(fetch_with_timeout(api, 1, seconds=0.05)) is None
    assert time.perf_counter() - started < 0.8, "should give up after the timeout, not wait 1s"


def test_fetch_all_settled_splits_successes_and_errors():
    api = FlakyPayerAPI(failing_ids={2})
    successes, errors = asyncio.run(fetch_all_settled(api, [1, 2, 3]))
    assert set(successes) == {1, 3}
    assert successes[3] == {"patient_id": 3, "plan": "PPO"}
    assert errors == {2: "payer timeout for 2"}


def test_fetch_all_settled_is_concurrent():
    api = FlakyPayerAPI()
    asyncio.run(fetch_all_settled(api, [1, 2, 3, 4]))
    assert api.max_in_flight == 4


def test_fetch_limited_respects_limit_and_order():
    api = FlakyPayerAPI()
    ids = list(range(10))
    results = asyncio.run(fetch_limited(api, ids, limit=3))
    assert [r["patient_id"] for r in results] == ids
    assert api.max_in_flight == 3


def test_fetch_limited_empty():
    assert asyncio.run(fetch_limited(FlakyPayerAPI(), [], limit=2)) == []
