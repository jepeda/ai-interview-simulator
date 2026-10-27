"""Drill 14 - async / await basics.

TS mental model: `async def` / `await` look like JS, with two big differences.
Calling an async function WITHOUT await gives a coroutine object, like an
un-awaited Promise, except its body never even starts running. And there is no
implicit event loop: sync code starts one with asyncio.run(...) once, at the edge.

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen async cheat sheet.
"""

import asyncio


# FakeEligibilityAPI is provided (don't edit): a stand-in for a slow payer API.
# fetch(patient_id) sleeps `delay` seconds (0.02 by default), then returns
#   {"patient_id": patient_id, "eligible": patient_id % 2 == 0}   even ids are eligible
# It records every id in .calls and the peak number of simultaneous fetches in
# .max_in_flight, which is how the tests check for concurrency.
class FakeEligibilityAPI:
    def __init__(self, delay: float = 0.02) -> None:
        self.delay = delay
        self.calls: list[int] = []
        self.in_flight = 0
        self.max_in_flight = 0

    async def fetch(self, patient_id: int) -> dict:
        self.calls.append(patient_id)
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            return {"patient_id": patient_id, "eligible": patient_id % 2 == 0}
        finally:
            self.in_flight -= 1


# ── Q1 · is_eligible ─────────────────────────────────────────── fix the bug ──
# Ask the payer whether one patient is covered. Must stay an `async def`.
# Return the "eligible" flag (a bool) from api.fetch(patient_id).
#
#   await is_eligible(api, 2)   -> True
#   await is_eligible(api, 3)   -> False
#
# Today: raises TypeError: 'coroutine' object is not subscriptable.
async def is_eligible(api: FakeEligibilityAPI, patient_id: int) -> bool:
    result = api.fetch(patient_id)
    return result["eligible"]


# ── Q2 · check_many ──────────────────────────────────────────── fix the bug ──
# The front desk checks a whole day's patients at once. Return
# {patient_id: eligible} for every id in `patient_ids`.
#
#   await check_many(api, [1, 2, 3, 4])   -> {1: False, 2: True, 3: False, 4: True}
#   await check_many(api, [])             -> {}
#
# All lookups must be in flight at the same time: for 5 ids the test requires
# api.max_in_flight == 5 (so 5 ids take ~1 delay, not 5).
#
# Today: even with Q1 fixed, it awaits each lookup before starting the next
# (max_in_flight == 1).
# TS equivalent: `Promise.all(ids.map(id => isEligible(api, id)))`
async def check_many(api: FakeEligibilityAPI, patient_ids: list[int]) -> dict[int, bool]:
    results = {}
    for patient_id in patient_ids:
        results[patient_id] = await is_eligible(api, patient_id)
    return results


# ── Q3 · check_many_sync ───────────────────────────────────────── implement ──
# A plain (non-async) function for synchronous callers such as a CLI script
# or a cron job. Create a fresh FakeEligibilityAPI() (default delay), run
# check_many with it, and return its dict.
#
#   check_many_sync([10, 11])   -> {10: True, 11: False}    a dict, not a coroutine
def check_many_sync(patient_ids: list[int]) -> dict[int, bool]:
    raise NotImplementedError
