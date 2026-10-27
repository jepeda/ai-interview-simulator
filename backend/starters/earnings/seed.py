"""Demo data for the running app (and for the support ticket you're debugging).

Sessions come from each provider's recurring clients (weekly or every other week), minus time off,
plus a few one-off no-shows and cancellations. Everything on or before AS_OF has happened; later
sessions are still booked. Acme Health pays each week's sessions on the Friday of the following week.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from earnings.models import Adjustment, Appointment, ContractedRate, Provider, SessionStatus

AS_OF = date(2026, 10, 23)
SEED_UNTIL = date(2026, 11, 30)

PROVIDERS = [
    # id, name, npi, license, state
    (1, "Rosa Delgado, LCSW", "1730492851", "LCSW", "TX"),
    (2, "Dr. Ethan Marsh, PsyD", "1528374619", "PsyD", "CO"),
    (3, "Naomi Feld, LPC", "1902846372", "LPC", "GA"),
]

# provider id -> [(payer, cpt, rate cents, effective date, entered at (UTC), note)], in entry order
RATES: dict[int, list[tuple[str, str, int, str, str, str]]] = {
    1: [
        ("Aetna", "90791", 19000, "2026-01-01", "2025-12-08 15:12", "2026 contract"),
        ("Aetna", "90834", 12500, "2026-01-01", "2025-12-08 15:12", "2026 contract"),
        ("Aetna", "90837", 14800, "2026-01-01", "2025-12-08 15:13", "2026 contract"),
        ("Cigna", "90791", 18000, "2026-01-01", "2025-12-09 10:41", "2026 contract"),
        ("Cigna", "90834", 12800, "2026-01-01", "2025-12-09 10:41", "2026 contract"),
        ("Cigna", "90837", 16000, "2026-01-01", "2025-12-09 10:42", "2026 contract"),
        ("Optum", "90791", 17500, "2026-01-01", "2025-12-09 11:05", "2026 contract"),
        ("Optum", "90834", 11800, "2026-01-01", "2025-12-09 11:05", "2026 contract"),
        ("Optum", "90837", 15000, "2026-01-01", "2025-12-09 11:06", "2026 contract"),
        ("Aetna", "90791", 20500, "2026-07-01", "2026-05-14 17:30", "Aetna mid-year rate increase"),
        ("Aetna", "90834", 13600, "2026-07-01", "2026-05-14 17:30", "Aetna mid-year rate increase"),
        ("Aetna", "90837", 17200, "2026-07-01", "2026-05-14 17:31", "Aetna mid-year rate increase"),
        ("Optum", "90837", 15500, "2026-09-01", "2026-08-03 14:02", "Optum rate increase"),
        ("Aetna", "90837", 15800, "2026-01-01", "2026-08-20 19:48", "Correction: 2026 contract rate is $158.00"),
        ("Aetna", "90834", 14200, "2027-01-01", "2026-10-02 16:20", "2027 rate increase"),
        ("Aetna", "90837", 18000, "2027-01-01", "2026-10-02 16:20", "2027 rate increase"),
    ],
    2: [
        ("Cigna", "90791", 21000, "2026-01-01", "2025-12-10 09:15", "2026 contract"),
        ("Cigna", "90834", 14000, "2026-01-01", "2025-12-10 09:15", "2026 contract"),
        ("Cigna", "90837", 17500, "2026-01-01", "2025-12-10 09:16", "2026 contract"),
        ("Optum", "90791", 19500, "2026-01-01", "2025-12-10 09:30", "2026 contract"),
        ("Optum", "90837", 16000, "2026-01-01", "2025-12-10 09:31", "2026 contract"),
        ("Optum", "90837", 16800, "2026-04-01", "2026-03-02 13:00", "Optum rate increase"),
        ("Cigna", "90837", 18200, "2026-12-01", "2026-10-14 18:45", "Cigna rate increase"),
    ],
    3: [
        ("Aetna", "90791", 17000, "2026-01-01", "2025-12-11 16:00", "2026 contract"),
        ("Aetna", "90834", 11500, "2026-01-01", "2025-12-11 16:00", "2026 contract"),
        ("Aetna", "90837", 14000, "2026-01-01", "2025-12-11 16:01", "2026 contract"),
        ("Optum", "90791", 16500, "2026-01-01", "2025-12-11 16:20", "2026 contract"),
        ("Optum", "90837", 13800, "2026-01-01", "2025-12-11 16:21", "2026 contract"),
        ("Aetna", "90837", 14600, "2026-07-01", "2026-06-01 12:10", "Aetna mid-year rate increase"),
    ],
}

# provider id -> [(client, payer, cpt, first session, until, every n weeks, start time)]
# A client's first session is the intake (90791); the rest use `cpt`.
CLIENTS: dict[int, list[tuple[str, str, str, str, str, int, str]]] = {
    1: [
        ("Nguyen, Linh", "Aetna", "90837", "2026-01-05", "2026-11-30", 1, "10:00"),
        ("Brooks, Tamara", "Cigna", "90837", "2026-01-06", "2026-06-30", 1, "16:00"),
        ("Okafor, Ada", "Aetna", "90837", "2026-01-14", "2026-11-30", 2, "14:00"),
        ("Reyes, Marisol", "Aetna", "90834", "2026-02-05", "2026-11-30", 1, "09:00"),
        ("Haddad, Rami", "Optum", "90837", "2026-03-06", "2026-11-30", 2, "11:00"),
        ("Lindqvist, Freya", "Cigna", "90834", "2026-09-08", "2026-11-30", 1, "16:00"),
    ],
    2: [
        ("Park, Hannah", "Cigna", "90837", "2026-01-07", "2026-11-30", 1, "12:00"),
        ("Wright, Owen", "Optum", "90837", "2026-02-03", "2026-11-30", 1, "18:00"),
        ("Silva, Bruno", "Cigna", "90834", "2026-04-09", "2026-09-24", 2, "17:00"),
    ],
    3: [
        ("Alvarez, Diego", "Aetna", "90837", "2026-01-12", "2026-11-30", 1, "09:30"),
        ("Kowalski, Erin", "Optum", "90837", "2026-02-18", "2026-11-30", 2, "13:00"),
        ("Okoro, Chidi", "Aetna", "90834", "2026-05-06", "2026-11-30", 1, "15:00"),
    ],
}

# provider id -> [(first day, last day)] the provider isn't seeing clients
TIME_OFF = {
    1: [("2026-08-01", "2026-08-31")],  # leave
    2: [("2026-06-22", "2026-07-05")],
    3: [("2026-12-21", "2026-12-31")],
}

# (provider id, client, date) -> status, for sessions that didn't happen as booked
EXCEPTIONS = {
    (1, "Nguyen, Linh", "2026-03-16"): SessionStatus.NO_SHOW,
    (1, "Nguyen, Linh", "2026-05-25"): SessionStatus.CANCELLED,
    (1, "Nguyen, Linh", "2026-09-07"): SessionStatus.CANCELLED,
    (1, "Reyes, Marisol", "2026-07-02"): SessionStatus.NO_SHOW,
    (1, "Reyes, Marisol", "2026-10-08"): SessionStatus.CANCELLED,
    (1, "Haddad, Rami", "2026-04-17"): SessionStatus.NO_SHOW,
    (2, "Park, Hannah", "2026-02-18"): SessionStatus.NO_SHOW,
    (2, "Wright, Owen", "2026-09-01"): SessionStatus.CANCELLED,
    (3, "Okoro, Chidi", "2026-06-10"): SessionStatus.NO_SHOW,
}

ADJUSTMENTS = [
    # provider id, effective date, cents, reason
    (1, date(2026, 3, 20), 25000, "Telehealth platform stipend (Q1)"),
    (1, date(2026, 8, 28), 34000, "Back pay: 2026 Aetna 90837 rate correction (Jan-Jun sessions)"),
    (1, date(2026, 9, 18), -17200, "Recoupment: Aetna duplicate claim (Jul 13 session)"),
    (2, date(2026, 5, 15), -16800, "Recoupment: Optum post-payment audit"),
]


def _day(raw: str) -> date:
    return date.fromisoformat(raw)


def pay_day(service_date: date) -> date:
    """The Friday of the week after the session's week (weeks run Monday-Sunday)."""
    next_monday = service_date + timedelta(days=7 - service_date.weekday())
    return next_monday + timedelta(days=4)


def _off(provider_id: int, day: date) -> bool:
    return any(_day(a) <= day <= _day(b) for a, b in TIME_OFF.get(provider_id, []))


def generate_appointments(provider_id: int) -> list[Appointment]:
    appointments = []
    for client, payer, cpt, first, until, every, start in CLIENTS[provider_id]:
        day, last = _day(first), min(_day(until), SEED_UNTIL)
        while day <= last:
            if not _off(provider_id, day):
                status = EXCEPTIONS.get((provider_id, client, day.isoformat()))
                if status is None:
                    status = SessionStatus.COMPLETED if day <= AS_OF else SessionStatus.SCHEDULED
                paid = pay_day(day) if status == SessionStatus.COMPLETED and pay_day(day) <= AS_OF else None
                appointments.append(
                    Appointment(
                        provider_id=provider_id,
                        client_name=client,
                        service_date=day,
                        start_time=time.fromisoformat(start),
                        cpt_code="90791" if day == _day(first) else cpt,
                        payer=payer,
                        status=status,
                        paid_on=paid,
                    )
                )
            day += timedelta(weeks=every)
    return sorted(appointments, key=lambda a: (a.service_date, a.start_time))


def seed(db: Session) -> None:
    for provider_id, name, npi, license_, state in PROVIDERS:
        db.add(Provider(id=provider_id, name=name, npi=npi, license=license_, state=state))
    for provider_id, entries in RATES.items():
        for payer, cpt, cents, effective, entered, note in entries:
            db.add(
                ContractedRate(
                    provider_id=provider_id,
                    payer=payer,
                    cpt_code=cpt,
                    rate_cents=cents,
                    effective_date=_day(effective),
                    created_at=datetime.fromisoformat(entered),
                    note=note,
                )
            )
    for provider_id in CLIENTS:
        db.add_all(generate_appointments(provider_id))
    for provider_id, day, cents, reason in ADJUSTMENTS:
        db.add(Adjustment(provider_id=provider_id, effective_date=day, amount_cents=cents, reason=reason))
    db.commit()


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Provider.id).limit(1)) is None:
        seed(db)
