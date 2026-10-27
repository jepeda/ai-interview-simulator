"""Pay statements: what a provider is paid for one pay period, and the list of their periods."""

from sqlalchemy.orm import Session

from payouts.models import Provider
from payouts.repositories import adjustments as adjustments_repo
from payouts.repositories import appointments as appointments_repo
from payouts.repositories import providers as providers_repo
from payouts.schemas import AdjustmentLine, PeriodSummary, ProviderOut, Statement, StatementLine
from payouts.services.paydates import expected_pay_date
from payouts.services.periods import (
    PayPeriod,
    local_service_date,
    period_containing,
    period_of,
    query_bounds,
)
from payouts.services.rates import payable_for
from payouts.timeutil import from_db, zone


def _period_label(period: PayPeriod) -> str:
    return f"{period.start.isoformat()} to {period.end.isoformat()}"


def _own_statement(db: Session, provider: Provider, period: PayPeriod) -> Statement:
    """The period's sessions and adjustments, without any carryover from earlier periods."""
    tz = zone(provider.timezone)
    fees = providers_repo.fee_table(db, provider.id)
    start, end = query_bounds(period, tz)

    lines: list[StatementLine] = []
    for appt in appointments_repo.list_between(db, provider.id, start, end):
        payable = payable_for(appt, provider, fees)
        if payable is None:
            continue
        lines.append(
            StatementLine(
                appointment_id=appt.id,
                service_date=local_service_date(appt, tz),
                starts_at=from_db(appt.starts_at),
                client_name=appt.client_name,
                cpt_code=appt.cpt_code,
                payer=appt.payer,
                status=appt.status,
                kind=payable.kind,
                amount_cents=payable.amount_cents,
            )
        )

    adjustments = [
        AdjustmentLine(id=a.id, effective_date=a.effective_date, reason=a.reason, amount_cents=a.amount_cents)
        for a in adjustments_repo.list_between(db, provider.id, period.start, period.end)
    ]
    total = sum(line.amount_cents for line in lines) + sum(a.amount_cents for a in adjustments)
    return Statement(
        provider=ProviderOut.model_validate(provider),
        period_start=period.start,
        period_end=period.end,
        lines=lines,
        adjustments=adjustments,
        total_cents=total,
        payout_cents=max(total, 0),
        pay_date=expected_pay_date(period.end),
    )


def build_statement(db: Session, provider: Provider, period: PayPeriod) -> Statement:
    """Walk forward from the provider's first period, carrying any negative balance along."""
    history = [p for p in active_periods(db, provider) if p < period]
    carry = 0
    previous: PayPeriod | None = None
    for past in [*history, period]:
        statement = _own_statement(db, provider, past)
        if carry < 0 and previous is not None:
            statement.adjustments.insert(
                0,
                AdjustmentLine(
                    id=None,
                    effective_date=past.start,
                    reason=f"Carryover from {_period_label(previous)}",
                    amount_cents=carry,
                ),
            )
            statement.total_cents += carry
            statement.payout_cents = max(statement.total_cents, 0)
        carry = min(statement.total_cents, 0)
        previous = past
        if past == period:
            return statement
    raise AssertionError("unreachable")


def active_periods(db: Session, provider: Provider) -> list[PayPeriod]:
    """Every pay period with at least one appointment or adjustment, oldest first."""
    tz = zone(provider.timezone)
    periods = {period_of(a, tz) for a in appointments_repo.list_for_provider(db, provider.id)}
    for adj in adjustments_repo.list_for_provider(db, provider.id):
        periods.add(period_containing(adj.effective_date))
    return sorted(periods)


def list_periods(db: Session, provider: Provider) -> list[PeriodSummary]:
    """Newest first, the way the portal shows them."""
    summaries = []
    for period in active_periods(db, provider):
        statement = build_statement(db, provider, period)
        summaries.append(
            PeriodSummary(
                period_start=period.start,
                period_end=period.end,
                session_count=len(statement.lines),
                total_cents=statement.total_cents,
                payout_cents=statement.payout_cents,
                pay_date=statement.pay_date,
            )
        )
    return list(reversed(summaries))
