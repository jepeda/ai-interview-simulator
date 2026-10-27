"""Demo data for the running app (http://127.0.0.1:8712/docs). Tests build their own data."""

from datetime import date, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from booking.models import AvailabilityWindow, Patient, Provider, ProviderLicense, ProviderPayer, Specialty


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Provider)):
        return

    later = date.today() + timedelta(days=365)
    specialties = {
        slug: Specialty(slug=slug, name=name)
        for slug, name in [
            ("anxiety", "Anxiety"),
            ("depression", "Depression"),
            ("trauma", "Trauma & PTSD"),
            ("couples", "Couples"),
        ]
    }

    def provider(first, last, credential, tz, rate, rating, states, payers, specs, windows, accepting=True):
        p = Provider(
            first_name=first, last_name=last, credential=credential, timezone=tz,
            session_rate_cents=rate, rating=rating, accepting_new_patients=accepting,
        )
        p.licenses = [ProviderLicense(state=s, expires_on=later) for s in states]
        p.payers = [ProviderPayer(payer_name=name) for name in payers]
        p.specialties = [specialties[s] for s in specs]
        p.availability = [
            AvailabilityWindow(weekday=wd, start_time=time(sh), end_time=time(eh)) for wd, sh, eh in windows
        ]
        return p

    weekdays_9_to_12 = [(wd, 9, 12) for wd in range(5)]
    db.add_all([
        provider("Maya", "Rivera", "LCSW", "America/New_York", 15000, 4.9, ["NY", "NJ"],
                 ["Aetna", "Cigna"], ["anxiety", "depression"], weekdays_9_to_12),
        provider("Sam", "Okoro", "PhD", "America/Chicago", 20000, 4.7, ["NY", "IL"],
                 ["Aetna"], ["trauma", "anxiety"], [(0, 13, 17), (2, 13, 17)]),
        provider("Lena", "Kai", "LMFT", "Pacific/Honolulu", 14000, None, ["NY", "HI", "CA"],
                 ["UnitedHealthcare"], ["couples"], [(0, 18, 21), (3, 18, 21)]),
        provider("Ari", "Stone", "LCSW", "America/Los_Angeles", 13000, 4.2, ["CA"],
                 ["Aetna", "Blue Shield"], ["depression"], weekdays_9_to_12),
        provider("Noor", "Haddad", "PsyD", "America/New_York", 22000, 5.0, ["NY"],
                 ["Cigna"], ["anxiety"], weekdays_9_to_12, accepting=False),
    ])
    db.add_all([
        Patient(first_name="Jordan", last_name="Lee", state="NY", payer_name="Aetna"),
        Patient(first_name="Casey", last_name="Diaz", state="CA", payer_name=None),
        Patient(first_name="Riley", last_name="Park", state="NY", payer_name="Cigna"),
    ])
    db.commit()
