"""Demo data for the running app (and for the support ticket you're debugging).

Claims are what we billed. Remittances are REPLAYED through the real posting service, exactly as
the clearinghouse delivered them (amounts are dollar strings, like in the 835 files), so what you
see in the portal is what posting produced. Delete backend/data/remits.db to re-run it.
"""

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from remits.models import Claim, FeeSchedule, Provider
from remits.schemas import EraIn
from remits.services.posting import post_remittance

PROVIDERS = [
    (1, "Dr. Maya Patel, PsyD", "1639204817"),
    (2, "Jordan Ellis, LCSW", "1295837461"),
    (3, "Sam Okafor, LPC", "1487263950"),
]

# Acme Health's chargemaster: what we bill every payer, per CPT code.
BILLED = {"90791": 25000, "90834": 18000, "90837": 20000}

# Contracted allowed amounts, per payer and CPT code.
FEE_SCHEDULES = {
    "Aetna": {"90791": 19000, "90834": 12115, "90837": 16817},
    "Cigna": {"90791": 18240, "90834": 11500, "90837": 15875},
    "Optum": {"90791": 17650, "90834": 11286, "90837": 16217},
}

# claim number, provider id, patient, payer, cpt, date of service
CLAIMS = [
    ("HW-1028", 2, "Park, Hannah", "Aetna", "90791", date(2026, 7, 14)),
    ("HW-1029", 2, "Wright, Owen", "Aetna", "90837", date(2026, 9, 8)),
    ("HW-1030", 1, "Nguyen, Linh", "Aetna", "90837", date(2026, 9, 9)),
    ("HW-1031", 3, "Lindqvist, Freya", "Aetna", "90834", date(2026, 9, 10)),
    ("HW-1032", 2, "Park, Hannah", "Aetna", "90834", date(2026, 9, 15)),
    ("HW-1033", 1, "Okoro, Chidi", "Cigna", "90837", date(2026, 9, 14)),
    ("HW-1034", 1, "Brooks, Tamara", "Cigna", "90834", date(2026, 9, 16)),
    ("HW-1035", 2, "Silva, Bruno", "Cigna", "90837", date(2026, 9, 17)),
    ("HW-1036", 1, "Okoro, Chidi", "Cigna", "90837", date(2026, 8, 17)),
    ("HW-1040", 1, "Alvarez, Diego", "Optum", "90834", date(2026, 9, 21)),
    ("HW-1041", 3, "Haddad, Rami", "Optum", "90837", date(2026, 9, 22)),
    ("HW-1042", 1, "Reyes, Marisol", "Optum", "90837", date(2026, 9, 24)),
    ("HW-1043", 1, "Alvarez, Diego", "Optum", "90837", date(2026, 9, 28)),
    ("HW-1044", 3, "Haddad, Rami", "Optum", "90837", date(2026, 9, 29)),
    ("HW-1045", 1, "Kowalski, Erin", "Optum", "90791", date(2026, 9, 30)),
    ("HW-1046", 1, "Reyes, Marisol", "Optum", "90834", date(2026, 10, 1)),
    ("HW-1050", 1, "Nguyen, Linh", "Aetna", "90837", date(2026, 10, 5)),
    ("HW-1051", 2, "Wright, Owen", "Aetna", "90837", date(2026, 10, 6)),
    ("HW-1052", 3, "Lindqvist, Freya", "Aetna", "90834", date(2026, 10, 7)),
    ("HW-1053", 2, "Park, Hannah", "Aetna", "90834", date(2026, 10, 8)),
    ("HW-1054", 1, "Okoro, Chidi", "Cigna", "90837", date(2026, 10, 12)),
    ("HW-1055", 1, "Reyes, Marisol", "Optum", "90837", date(2026, 10, 13)),
    ("HW-1056", 3, "Haddad, Rami", "Optum", "90837", date(2026, 10, 14)),
    ("HW-1057", 2, "Silva, Bruno", "Cigna", "90837", date(2026, 10, 15)),
]


def _line(claim: str, billed: str, paid: str, *adjustments: tuple[str, str, str], status: str = "1") -> dict:
    return {
        "claim_number": claim,
        "status_code": status,
        "billed": billed,
        "paid": paid,
        "adjustments": [{"group": g, "reason": r, "amount": a} for g, r, a in adjustments],
    }


AETNA_OCT_2 = {
    "payer": "Aetna",
    "trace_number": "1000738214",
    "payment_method": "ACH",
    "paid_on": "2026-10-02",
    "total_paid": "367.49",
    "claims": [
        _line("HW-1028", "250.00", "0.00", ("CO", "29", "250.00"), status="4"),
        _line("HW-1029", "200.00", "138.17", ("CO", "45", "31.83"), ("PR", "3", "30.00")),
        _line("HW-1030", "200.00", "138.17", ("CO", "45", "31.83"), ("PR", "3", "30.00")),
        _line("HW-1031", "180.00", "91.15", ("CO", "45", "58.85"), ("PR", "3", "30.00")),
        _line("HW-1032", "180.00", "0.00", ("CO", "16", "180.00"), status="4"),
    ],
}

CIGNA_OCT_6 = {
    "payer": "Cigna",
    "trace_number": "004417920",
    "payment_method": "CHK",
    "paid_on": "2026-10-06",
    "total_paid": "345.40",
    "claims": [
        _line("HW-1033", "200.00", "127.00", ("CO", "45", "41.25"), ("PR", "2", "31.75")),
        _line("HW-1034", "180.00", "92.00", ("CO", "45", "65.00"), ("PR", "2", "23.00")),
        _line("HW-1035", "200.00", "126.40", ("CO", "45", "42.00"), ("PR", "2", "31.60")),
        _line("HW-1036", "200.00", "0.00", ("CO", "197", "200.00"), status="4"),
    ],
}

OPTUM_OCT_9 = {
    "payer": "Optum",
    "trace_number": "1102948731",
    "payment_method": "ACH",
    "paid_on": "2026-10-09",
    "total_paid": "594.39",
    "claims": [
        _line("HW-1040", "180.00", "87.86", ("CO", "45", "67.14"), ("PR", "3", "25.00")),
        _line("HW-1041", "200.00", "137.17", ("CO", "45", "37.83"), ("PR", "3", "25.00")),
        _line("HW-1042", "200.00", "137.17", ("CO", "45", "37.83"), ("PR", "3", "25.00")),
        _line("HW-1043", "200.00", "137.17", ("CO", "45", "37.83"), ("PR", "3", "25.00")),
        _line("HW-1044", "200.00", "137.17", ("CO", "45", "37.83"), ("PR", "3", "25.00")),
        _line("HW-1045", "250.00", "0.00", ("CO", "45", "73.50"), ("PR", "1", "176.50")),
        _line("HW-1046", "180.00", "0.00", ("CO", "197", "180.00"), status="4"),
    ],
    "remit_adjustments": [{"code": "WO", "reference": "HW-0987", "amount": "-42.15"}],
}

AETNA_OCT_23 = {
    "payer": "Aetna",
    "trace_number": "1000741187",
    "payment_method": "ACH",
    "paid_on": "2026-10-23",
    "total_paid": "439.46",
    "claims": [
        _line("HW-1050", "200.00", "128.58", ("CO", "45", "41.42"), ("PR", "3", "30.00")),
        _line("HW-1051", "200.00", "128.58", ("CO", "45", "41.42"), ("PR", "3", "30.00")),
        _line("HW-1052", "180.00", "91.15", ("CO", "45", "58.85"), ("PR", "3", "30.00")),
        _line("HW-1053", "180.00", "91.15", ("CO", "45", "58.85"), ("PR", "3", "30.00")),
    ],
}

# Every ERA file in the order the clearinghouse delivered it, with when it arrived (UTC).
# Optum's clearinghouse had an outage and re-sent its Oct 9 file on Oct 12.
DELIVERIES = [
    (AETNA_OCT_2, datetime(2026, 10, 2, 14, 5, tzinfo=UTC)),
    (CIGNA_OCT_6, datetime(2026, 10, 6, 15, 40, tzinfo=UTC)),
    (OPTUM_OCT_9, datetime(2026, 10, 9, 13, 12, tzinfo=UTC)),
    (OPTUM_OCT_9, datetime(2026, 10, 12, 9, 47, tzinfo=UTC)),
    (AETNA_OCT_23, datetime(2026, 10, 23, 14, 2, tzinfo=UTC)),
]


def seed(db: Session) -> None:
    for provider_id, name, npi in PROVIDERS:
        db.add(Provider(id=provider_id, name=name, npi=npi))
    for payer, rates in FEE_SCHEDULES.items():
        for cpt, cents in rates.items():
            db.add(FeeSchedule(payer=payer, cpt_code=cpt, allowed_cents=cents))
    for number, provider_id, patient, payer, cpt, dos in CLAIMS:
        db.add(
            Claim(
                claim_number=number,
                provider_id=provider_id,
                patient_name=patient,
                payer=payer,
                cpt_code=cpt,
                date_of_service=dos,
                billed_cents=BILLED[cpt],
            )
        )
    db.commit()
    for era, received_at in DELIVERIES:
        post_remittance(db, EraIn.model_validate(era), received_at=received_at)


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Provider.id).limit(1)) is None:
        seed(db)
