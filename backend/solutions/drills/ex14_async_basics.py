"""Drill 14 - async / await basics (reference solution)."""

import asyncio


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


async def is_eligible(api: FakeEligibilityAPI, patient_id: int) -> bool:
    result = await api.fetch(patient_id)
    return result["eligible"]


async def check_many(api: FakeEligibilityAPI, patient_ids: list[int]) -> dict[int, bool]:
    flags = await asyncio.gather(*(is_eligible(api, pid) for pid in patient_ids))
    return dict(zip(patient_ids, flags, strict=True))


def check_many_sync(patient_ids: list[int]) -> dict[int, bool]:
    return asyncio.run(check_many(FakeEligibilityAPI(), patient_ids))
