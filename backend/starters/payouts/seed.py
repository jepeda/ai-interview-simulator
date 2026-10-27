"""Demo data for the running app (and for the support ticket you're debugging).

Appointment times below are written in each provider's LOCAL time, the way their calendar shows
them, and converted to naive UTC for storage.
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from payouts.models import Adjustment, Appointment, FeeSchedule, Provider, SessionStatus
from payouts.timeutil import to_db, zone

C, LC, NS, X = (
    SessionStatus.COMPLETED,
    SessionStatus.LATE_CANCEL,
    SessionStatus.NO_SHOW,
    SessionStatus.CANCELLED,
)

PROVIDERS = [
    # id, name, npi, timezone, late-cancel fee
    (1, "Dr. Maya Patel, PsyD", "1639204817", "America/Los_Angeles", 7500),
    (2, "Jordan Ellis, LCSW", "1295837461", "America/New_York", 6000),
    (3, "Sam Okafor, LPC", "1487263950", "America/Chicago", 5000),
]

FEES = {
    1: {
        "Aetna": {"90791": 20000, "90834": 13000, "90837": 16500},
        "Cigna": {"90791": 21000, "90834": 13500, "90837": 17250},
        "Optum": {"90834": 12500, "90837": 15800},
        "Self-pay": {"90791": 22000, "90837": 18000},
    },
    2: {
        "Aetna": {"90791": 19000, "90834": 12000, "90837": 15000},
        "Cigna": {"90834": 12500, "90837": 15500},
        "Self-pay": {"90837": 17000},
    },
    3: {
        "Optum": {"90791": 18000, "90834": 11000, "90837": 15000},
        "Aetna": {"90837": 14500},
    },
}

# provider id -> (local "YYYY-MM-DD HH:MM", client, cpt, payer, status)
APPOINTMENTS: dict[int, list[tuple[str, str, str, str, SessionStatus]]] = {
    1: [
        ("2026-09-16 10:00", "Nguyen, Linh", "90837", "Aetna", C),
        ("2026-09-18 14:00", "Brooks, Tamara", "90834", "Cigna", C),
        ("2026-09-23 09:00", "Alvarez, Diego", "90837", "Optum", C),
        ("2026-09-25 16:00", "Nguyen, Linh", "90837", "Aetna", LC),
        ("2026-09-30 17:30", "Brooks, Tamara", "90834", "Cigna", C),
        ("2026-10-01 10:00", "Kowalski, Erin", "90791", "Self-pay", C),
        ("2026-10-02 11:00", "Nguyen, Linh", "90837", "Aetna", C),
        ("2026-10-06 13:00", "Okoro, Chidi", "90837", "Cigna", C),
        ("2026-10-07 09:30", "Alvarez, Diego", "90834", "Optum", C),
        ("2026-10-08 15:00", "Nguyen, Linh", "90837", "Aetna", NS),
        ("2026-10-09 10:00", "Brooks, Tamara", "90834", "Cigna", C),
        ("2026-10-12 12:00", "Okoro, Chidi", "90837", "Cigna", X),
        ("2026-10-13 12:00", "Nguyen, Linh", "90837", "Aetna", C),
        ("2026-10-14 16:00", "Alvarez, Diego", "90837", "Optum", C),
        ("2026-10-15 18:30", "Reyes, Marisol", "90837", "Aetna", C),
        ("2026-10-16 10:00", "Nguyen, Linh", "90837", "Aetna", C),
        ("2026-10-20 13:00", "Brooks, Tamara", "90834", "Cigna", C),
        ("2026-10-21 09:00", "Kowalski, Erin", "90837", "Self-pay", C),
        ("2026-10-22 14:00", "Alvarez, Diego", "90837", "Optum", LC),
        ("2026-10-27 11:00", "Reyes, Marisol", "90834", "Aetna", C),
        ("2026-10-29 15:00", "Okoro, Chidi", "90837", "Cigna", C),
        ("2026-10-30 17:00", "Nguyen, Linh", "90837", "Aetna", C),
        ("2026-11-02 10:00", "Nguyen, Linh", "90837", "Aetna", C),
        ("2026-11-05 13:00", "Brooks, Tamara", "90834", "Cigna", C),
        ("2026-11-10 09:00", "Alvarez, Diego", "90837", "Optum", C),
        ("2026-11-12 15:00", "Reyes, Marisol", "90837", "Aetna", C),
        ("2026-11-13 11:00", "Kowalski, Erin", "90837", "Self-pay", C),
        ("2026-11-16 10:00", "Okoro, Chidi", "90837", "Cigna", C),
        ("2026-11-19 14:00", "Reyes, Marisol", "90834", "Aetna", C),
        ("2026-11-24 09:00", "Alvarez, Diego", "90837", "Optum", C),
        ("2026-11-30 17:30", "Nguyen, Linh", "90837", "Aetna", C),
    ],
    2: [
        ("2026-10-01 09:00", "Park, Hannah", "90791", "Aetna", C),
        ("2026-10-06 18:00", "Wright, Owen", "90837", "Cigna", C),
        ("2026-10-08 12:00", "Park, Hannah", "90834", "Aetna", C),
        ("2026-10-13 19:00", "Wright, Owen", "90837", "Cigna", LC),
        ("2026-10-15 21:00", "Silva, Bruno", "90837", "Self-pay", C),
        ("2026-10-20 18:00", "Wright, Owen", "90837", "Cigna", C),
        ("2026-10-22 12:00", "Park, Hannah", "90834", "Aetna", C),
        ("2026-10-31 20:30", "Silva, Bruno", "90837", "Self-pay", C),
        ("2026-11-03 18:00", "Wright, Owen", "90837", "Cigna", C),
        ("2026-11-12 12:00", "Park, Hannah", "90834", "Aetna", NS),
        ("2026-11-17 18:00", "Wright, Owen", "90837", "Cigna", C),
    ],
    3: [
        ("2026-10-02 10:00", "Haddad, Rami", "90791", "Optum", C),
        ("2026-10-09 10:00", "Haddad, Rami", "90837", "Optum", C),
        ("2026-10-14 15:00", "Lindqvist, Freya", "90837", "Aetna", C),
        ("2026-10-19 10:00", "Haddad, Rami", "90837", "Optum", C),
        ("2026-10-26 10:00", "Haddad, Rami", "90837", "Optum", C),
        ("2026-11-02 10:00", "Haddad, Rami", "90837", "Optum", C),
        ("2026-11-05 15:00", "Lindqvist, Freya", "90837", "Aetna", C),
        ("2026-11-09 10:00", "Haddad, Rami", "90834", "Optum", C),
        ("2026-11-12 15:00", "Lindqvist, Freya", "90837", "Aetna", C),
        ("2026-11-16 10:00", "Haddad, Rami", "90837", "Optum", C),
        ("2026-11-19 15:00", "Lindqvist, Freya", "90837", "Aetna", C),
        ("2026-11-23 10:00", "Haddad, Rami", "90837", "Optum", C),
        ("2026-11-30 10:00", "Haddad, Rami", "90837", "Optum", C),
    ],
}

ADJUSTMENTS = [
    # provider id, effective date (local), cents, reason
    (1, date(2026, 10, 5), -3500, "Claim correction: Sep 16 session rebilled as 90834 (Aetna)"),
    (1, date(2026, 11, 20), 2500, "Telehealth platform stipend (Q4)"),
    (2, date(2026, 10, 19), -12500, "Duplicate payment reversal: Oct 8 session"),
    (3, date(2026, 10, 20), -120000, "Recoupment: Optum post-payment audit (July-August sessions)"),
]


def seed(db: Session) -> None:
    zones = {}
    for provider_id, name, npi, tz, late_fee in PROVIDERS:
        db.add(Provider(id=provider_id, name=name, npi=npi, timezone=tz, late_cancel_fee_cents=late_fee))
        zones[provider_id] = zone(tz)
    for provider_id, payers in FEES.items():
        for payer, rates in payers.items():
            for cpt, cents in rates.items():
                db.add(FeeSchedule(provider_id=provider_id, payer=payer, cpt_code=cpt, rate_cents=cents))
    for provider_id, rows in APPOINTMENTS.items():
        for local, client, cpt, payer, status in rows:
            starts = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=zones[provider_id])
            db.add(
                Appointment(
                    provider_id=provider_id,
                    client_name=client,
                    starts_at=to_db(starts),
                    cpt_code=cpt,
                    payer=payer,
                    status=status,
                )
            )
    for provider_id, day, cents, reason in ADJUSTMENTS:
        db.add(Adjustment(provider_id=provider_id, effective_date=day, amount_cents=cents, reason=reason))
    db.commit()


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Provider.id).limit(1)) is None:
        seed(db)
