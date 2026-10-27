"""Part 1: open slots (services/availability.py)."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from booking.services.availability import open_slots

NOW = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)  # same frozen time as conftest

NEW_YORK = ZoneInfo("America/New_York")
LOS_ANGELES = ZoneInfo("America/Los_Angeles")
MONDAY = date(2026, 11, 2)  # after DST ended: New York is UTC-5
TUESDAY = date(2026, 11, 3)


def local_starts(slots) -> list[str]:
    return [s.starts_at.strftime("%H:%M") for s in slots]


def test_windows_are_in_the_provider_timezone(make_provider):
    provider = make_provider(windows=[(0, "09:00", "12:00")])
    slots = open_slots(provider, MONDAY, NEW_YORK, [], NOW)
    assert local_starts(slots) == ["09:00", "10:00", "11:00"]
    assert slots[0].starts_at == datetime(2026, 11, 2, 14, 0, tzinfo=UTC)


def test_slots_are_returned_in_the_viewer_timezone(make_provider):
    provider = make_provider(windows=[(0, "09:00", "12:00")])
    slots = open_slots(provider, MONDAY, LOS_ANGELES, [], NOW)
    assert local_starts(slots) == ["06:00", "07:00", "08:00"]
    assert slots[0].starts_at.utcoffset() == LOS_ANGELES.utcoffset(datetime(2026, 11, 2, 12))


def test_daylight_saving_offsets(make_provider):
    provider = make_provider(windows=[(0, "09:00", "10:00")])
    summer = open_slots(provider, date(2026, 10, 26), NEW_YORK, [], NOW)  # EDT, UTC-4
    winter = open_slots(provider, MONDAY, NEW_YORK, [], NOW)  # EST, UTC-5
    assert summer[0].starts_at.astimezone(UTC).hour == 13
    assert winter[0].starts_at.astimezone(UTC).hour == 14


def test_session_must_end_inside_the_window(make_provider):
    provider = make_provider(windows=[(0, "09:00", "10:30"), (0, "13:00", "13:45")])
    assert local_starts(open_slots(provider, MONDAY, NEW_YORK, [], NOW)) == ["09:00"]


def test_partially_overlapping_appointment_blocks_slots(make_provider, make_patient, make_appointment):
    provider = make_provider(windows=[(0, "09:00", "12:00")])
    patient = make_patient()
    # 10:30-11:20 overlaps both the 10:00-10:50 and 11:00-11:50 slots
    booked = make_appointment(provider, patient, datetime(2026, 11, 2, 10, 30, tzinfo=NEW_YORK))
    slots = open_slots(provider, MONDAY, NEW_YORK, [booked], NOW)
    assert local_starts(slots) == ["09:00"]


def test_cancelled_appointments_do_not_block(make_provider, make_patient, make_appointment):
    provider = make_provider(windows=[(0, "09:00", "12:00")])
    patient = make_patient()
    cancelled = make_appointment(provider, patient, datetime(2026, 11, 2, 10, 0, tzinfo=NEW_YORK), status="cancelled")
    completed = make_appointment(provider, patient, datetime(2026, 11, 2, 11, 0, tzinfo=NEW_YORK), status="completed")
    slots = open_slots(provider, MONDAY, NEW_YORK, [cancelled, completed], NOW)
    assert local_starts(slots) == ["09:00", "10:00"]


def test_past_slots_are_excluded_but_now_is_still_open(make_provider):
    provider = make_provider(windows=[(0, "07:00", "10:00")])
    # NOW is 08:00 New York time on Monday 2026-10-26
    slots = open_slots(provider, date(2026, 10, 26), NEW_YORK, [], NOW)
    assert local_starts(slots) == ["08:00", "09:00"]


def test_viewer_day_can_include_the_providers_previous_evening(make_provider):
    # Honolulu (UTC-10) Monday 18:00-21:00 == New York (UTC-5) Monday 23:00 -> Tuesday 02:00
    provider = make_provider(tz="Pacific/Honolulu", windows=[(0, "18:00", "21:00")])
    assert local_starts(open_slots(provider, MONDAY, NEW_YORK, [], NOW)) == ["23:00"]
    assert local_starts(open_slots(provider, TUESDAY, NEW_YORK, [], NOW)) == ["00:00", "01:00"]


def test_slots_endpoint(client, make_provider):
    provider = make_provider(windows=[(0, "09:00", "11:00")])
    response = client.get(f"/providers/{provider.id}/slots", params={"date": "2026-11-02", "tz": "America/New_York"})
    assert response.status_code == 200
    body = response.json()
    assert body["timezone"] == "America/New_York"
    starts = [datetime.fromisoformat(s["starts_at"]) for s in body["slots"]]
    assert starts == [datetime(2026, 11, 2, 9, tzinfo=NEW_YORK), datetime(2026, 11, 2, 10, tzinfo=NEW_YORK)]


def test_slots_endpoint_rejects_unknown_timezone(client, make_provider):
    provider = make_provider()
    response = client.get(f"/providers/{provider.id}/slots", params={"date": "2026-11-02", "tz": "Mars/Base"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_timezone"
