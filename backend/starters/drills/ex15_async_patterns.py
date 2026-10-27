"""Drill 15 - async patterns: timeouts, partial failures, and concurrency limits.

TS mental model: the three patterns you'd reach for around a flaky third-party
API in Node, each with an asyncio equivalent:
  Promise.race([p, timeout(ms)])   -> give up on a slow call after N seconds
  Promise.allSettled(ps)           -> keep every result even when some calls fail
  p-limit(n)                       -> never more than n requests in flight at once

Each function has its question right above it. Make the tests pass:
Ctrl/Cmd+Enter runs them. The Quick ref tab has a one-screen async cheat sheet.
"""

import asyncio


# FlakyPayerAPI is provided (don't edit): a fake payer API.
# fetch(patient_id) takes 0.01 s, or 1.0 s for ids in `slow_ids`, then returns
#   {"patient_id": patient_id, "plan": "PPO"}
# For ids in `failing_ids` it raises ConnectionError(f"payer timeout for {patient_id}")
# instead. It tracks the peak number of simultaneous fetches in .max_in_flight.
class FlakyPayerAPI:
    def __init__(self, slow_ids: set[int] | None = None, failing_ids: set[int] | None = None) -> None:
        self.slow_ids = slow_ids or set()
        self.failing_ids = failing_ids or set()
        self.in_flight = 0
        self.max_in_flight = 0

    async def fetch(self, patient_id: int) -> dict:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(1.0 if patient_id in self.slow_ids else 0.01)
            if patient_id in self.failing_ids:
                raise ConnectionError(f"payer timeout for {patient_id}")
            return {"patient_id": patient_id, "plan": "PPO"}
        finally:
            self.in_flight -= 1


# ── Q1 · fetch_with_timeout ──────────────────────────────────── fix the bug ──
# The check-in screen can't hang on a slow payer. Return api.fetch(patient_id)'s
# result if it arrives within `seconds`; otherwise stop waiting and return None.
#
#   await fetch_with_timeout(FlakyPayerAPI(), 1, seconds=0.5)
#       -> {"patient_id": 1, "plan": "PPO"}
#   await fetch_with_timeout(FlakyPayerAPI(slow_ids={1}), 1, seconds=0.05)
#       -> None     and the whole call must return in < 0.8 s
#
# Giving up must actually stop waiting: don't let the 1 s fetch finish first.
# Only the timeout becomes None; other errors are not part of this question.
#
# Today: it always waits for the fetch (1 s for a slow id) and returns the dict.
# TS equivalent: `Promise.race([fetch(id), sleep(ms).then(() => null)])`
async def fetch_with_timeout(api: FlakyPayerAPI, patient_id: int, seconds: float) -> dict | None:
    return await api.fetch(patient_id)


# ── Q2 · fetch_all_settled ───────────────────────────────────── fix the bug ──
# Nightly re-verification of many patients. Fetch them all CONCURRENTLY; a
# failure for one patient must not lose the others' results.
# Return a tuple (successes, errors):
#   successes = {patient_id: result dict}      for fetches that worked
#   errors    = {patient_id: str(exception)}   for fetches that raised
#
#   api = FlakyPayerAPI(failing_ids={2})
#   await fetch_all_settled(api, [1, 2, 3])
#       -> ({1: {"patient_id": 1, "plan": "PPO"}, 3: {"patient_id": 3, "plan": "PPO"}},
#           {2: "payer timeout for 2"})
#
# All requests run at once: for 4 ids the test requires api.max_in_flight == 4.
#
# Today: the ConnectionError for id 2 escapes the function and the results for
# 1 and 3 are lost.
# TS equivalent: `Promise.allSettled(...)`, then split fulfilled / rejected.
async def fetch_all_settled(
    api: FlakyPayerAPI, patient_ids: list[int]
) -> tuple[dict[int, dict], dict[int, str]]:
    results = await asyncio.gather(*(api.fetch(pid) for pid in patient_ids))
    return dict(zip(patient_ids, results)), {}


# ── Q3 · fetch_limited ─────────────────────────────────────────── implement ──
# The payer rate-limits us. Fetch every id, but never have more than `limit`
# requests in flight at once, while still using all `limit` slots (requests
# run concurrently up to the cap, not one at a time).
# Return the result dicts as a list in the SAME order as `patient_ids`.
#
#   await fetch_limited(api, [0, 1, ..., 9], limit=3)
#       -> [{"patient_id": 0, ...}, {"patient_id": 1, ...}, ..., {"patient_id": 9, ...}]
#          and api.max_in_flight == 3     exactly the limit: not 10, not 1
#   await fetch_limited(api, [], limit=2)   -> []
#
# TS equivalent: `const limit = pLimit(3); Promise.all(ids.map(id => limit(() => fetch(id))))`
async def fetch_limited(api: FlakyPayerAPI, patient_ids: list[int], limit: int) -> list[dict]:
    raise NotImplementedError
