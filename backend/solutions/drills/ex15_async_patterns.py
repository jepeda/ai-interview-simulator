"""Drill 15 - async patterns (reference solution)."""

import asyncio


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


async def fetch_with_timeout(api: FlakyPayerAPI, patient_id: int, seconds: float) -> dict | None:
    try:
        async with asyncio.timeout(seconds):
            return await api.fetch(patient_id)
    except TimeoutError:
        return None


async def fetch_all_settled(
    api: FlakyPayerAPI, patient_ids: list[int]
) -> tuple[dict[int, dict], dict[int, str]]:
    results = await asyncio.gather(*(api.fetch(pid) for pid in patient_ids), return_exceptions=True)
    successes: dict[int, dict] = {}
    errors: dict[int, str] = {}
    for pid, result in zip(patient_ids, results, strict=True):
        if isinstance(result, Exception):
            errors[pid] = str(result)
        else:
            successes[pid] = result
    return successes, errors


async def fetch_limited(api: FlakyPayerAPI, patient_ids: list[int], limit: int) -> list[dict]:
    semaphore = asyncio.Semaphore(limit)

    async def one(pid: int) -> dict:
        async with semaphore:
            return await api.fetch(pid)

    return list(await asyncio.gather(*(one(pid) for pid in patient_ids)))
