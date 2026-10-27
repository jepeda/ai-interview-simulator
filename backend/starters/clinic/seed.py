"""Demo data. Dates are relative to today so every bug is visible whenever you run the app."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from clinic.models import Appointment, InsurancePlan, Patient


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute))


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Patient)):
        return

    today = date.today()

    aetna = InsurancePlan(
        payer_name="Aetna", plan_name="Choice POS II", copay_cents=2500,
        effective_date=date(2024, 1, 1), termination_date=None,
    )
    bcbs = InsurancePlan(
        payer_name="Blue Cross Blue Shield", plan_name="PPO Blue", copay_cents=3000,
        effective_date=date(2023, 7, 1), termination_date=today,  # today is the last covered day
    )
    cigna = InsurancePlan(
        payer_name="Cigna", plan_name="Open Access Plus", copay_cents=2000,
        effective_date=date(2022, 1, 1), termination_date=today - timedelta(days=120),
    )
    uhc = InsurancePlan(
        payer_name="UnitedHealthcare", plan_name="Choice Plus", copay_cents=1500,
        effective_date=today + timedelta(days=30), termination_date=None,
    )
    db.add_all([aetna, bcbs, cigna, uhc])

    def patient(first, last, dob, plan, member_id, status="active"):
        return Patient(
            first_name=first, last_name=last, date_of_birth=dob,
            email=f"{first}.{last}@example.com".lower(), insurance_plan=plan,
            member_id=member_id, status=status,
        )

    ada = patient("Ada", "King", date(1990, 12, 10), aetna, "W123456789")
    ben = patient("Ben", "Okafor", date(1985, 3, 22), bcbs, "XBC998877")
    db.add_all([
        ada,
        ben,
        patient("Carmen", "Diaz", date(1978, 6, 2), cigna, "CG55512", status=None),
        patient("Dev", "Patel", date(2001, 1, 15), None, None),
        patient("Elena", "Rossi", date(1993, 9, 30), uhc, "UHC-77001", status=None),
        patient("Farah", "Haddad", date(1988, 11, 5), aetna, None),
        patient("Gus", "Lindqvist", date(1969, 4, 18), aetna, "W000111222", status="archived"),
        patient("Hana", "Sato", date(1999, 7, 7), None, None, status=None),
        patient("Ivan", "Petrov", date(1982, 2, 28), bcbs, "XBC123123"),
        patient("Jada", "Brooks", date(1995, 5, 19), aetna, "W555000111"),
        patient("Kofi", "Mensah", date(1975, 10, 1), None, None),
    ])

    def appt(who, days, hour, minute=0, status="scheduled", provider="Dr. Maya Lee"):
        return Appointment(
            patient=who, provider_name=provider, starts_at=_at(today + timedelta(days=days), hour, minute),
            status=status,
        )

    db.add_all([
        appt(ada, -400, 10, status="completed"),
        appt(ada, -40, 10, status="completed"),
        appt(ada, -3, 16, 30, status="completed"),
        appt(ada, -1, 9, status="cancelled"),
        appt(ada, 2, 14),
        appt(ada, 2, 9),
        appt(ada, 25, 11, status="cancelled"),
        appt(ada, 70, 15),
        appt(ada, 95, 8, 30),
        appt(ben, -14, 13, provider="Dr. Sam Ortiz", status="completed"),
        appt(ben, 6, 17, provider="Dr. Sam Ortiz"),
        appt(ben, 120, 10, provider="Dr. Sam Ortiz"),
    ])
    db.commit()
