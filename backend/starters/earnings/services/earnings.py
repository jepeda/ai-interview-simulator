"""Earnings: completed sessions priced at the rate in effect on their date of service."""

from datetime import date

from sqlalchemy.orm import Session

from earnings.models import Provider, SessionStatus
from earnings.repositories import appointments as appointments_repo
from earnings.schemas import (
    EarningLine,
    EarningsSummary,
    MonthDetail,
    MonthEarnings,
    PayerEarnings,
    ProviderOut,
)
from earnings.services.months import Month, month_of
from earnings.services.rates import load_rate_table


def earning_lines(db: Session, provider: Provider, first_day: date, last_day: date) -> list[EarningLine]:
    """One line per completed session in [first_day, last_day], oldest first."""
    rates = load_rate_table(db, provider.id)
    lines = []
    for appt in appointments_repo.list_between(db, provider.id, first_day, last_day):
        if appt.status != SessionStatus.COMPLETED:
            continue
        lines.append(
            EarningLine(
                appointment_id=appt.id,
                service_date=appt.service_date,
                start_time=appt.start_time,
                client_name=appt.client_name,
                cpt_code=appt.cpt_code,
                payer=appt.payer,
                rate_cents=rates.rate_for(appt),
                paid_on=appt.paid_on,
            )
        )
    return lines


def year_summary(db: Session, provider: Provider, year: int) -> EarningsSummary:
    lines = earning_lines(db, provider, date(year, 1, 1), date(year, 12, 31))

    months: dict[Month, MonthEarnings] = {}
    payers: dict[str, PayerEarnings] = {}
    for line in lines:
        month = month_of(line.service_date)
        bucket = months.setdefault(month, MonthEarnings(month=month.key(), session_count=0, earned_cents=0))
        bucket.session_count += 1
        bucket.earned_cents += line.rate_cents
        payer = payers.setdefault(line.payer, PayerEarnings(payer=line.payer, session_count=0, earned_cents=0))
        payer.session_count += 1
        payer.earned_cents += line.rate_cents

    return EarningsSummary(
        provider=ProviderOut.model_validate(provider),
        year=year,
        session_count=len(lines),
        total_cents=sum(line.rate_cents for line in lines),
        months=[months[m] for m in sorted(months)],
        by_payer=sorted(payers.values(), key=lambda p: (-p.earned_cents, p.payer)),
    )


def month_detail(db: Session, provider: Provider, month: Month) -> MonthDetail:
    lines = earning_lines(db, provider, month.first_day, month.last_day)
    return MonthDetail(
        provider_id=provider.id,
        month=month.key(),
        session_count=len(lines),
        total_cents=sum(line.rate_cents for line in lines),
        lines=lines,
    )
