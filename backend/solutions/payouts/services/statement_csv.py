"""CSV export of a pay statement, for providers' accountants."""

import csv
import io

from payouts.schemas import Statement

COLUMNS = ["Date", "Client", "Service", "Payer", "Type", "Description", "Amount"]
TYPE_LABELS = {"session": "Session", "late_cancel": "Late cancel"}


def dollars(cents: int) -> str:
    """12345 -> "123.45", -3500 -> "-35.00" (integer math: no float rounding)."""
    sign = "-" if cents < 0 else ""
    whole, rest = divmod(abs(cents), 100)
    return f"{sign}{whole}.{rest:02d}"


def statement_csv(statement: Statement) -> str:
    rows: list[tuple[tuple, list[str]]] = []
    for line in statement.lines:
        rows.append(
            (
                (line.service_date, 0, line.starts_at),
                [
                    line.service_date.isoformat(),
                    line.client_name,
                    line.cpt_code,
                    line.payer,
                    TYPE_LABELS.get(line.kind, line.kind),
                    "",
                    dollars(line.amount_cents),
                ],
            )
        )
    for adj in statement.adjustments:
        rows.append(
            (
                (adj.effective_date, 1, None),
                [adj.effective_date.isoformat(), "", "", "", "Adjustment", adj.reason, dollars(adj.amount_cents)],
            )
        )
    rows.sort(key=lambda r: (r[0][0], r[0][1]))  # stable: lines are already in time order

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(COLUMNS)
    writer.writerows(cells for _, cells in rows)
    writer.writerow(["", "", "", "", "Total", "", dollars(statement.total_cents)])
    return out.getvalue()
