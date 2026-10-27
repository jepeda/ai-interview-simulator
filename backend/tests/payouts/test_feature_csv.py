"""Feature: download a pay statement as CSV (for providers' accountants)."""

import csv
import io
from datetime import date

from payouts_testkit import LATE_CANCEL_FEE

from payouts.models import SessionStatus

HEADER = ["Date", "Client", "Service", "Payer", "Type", "Description", "Amount"]


def get_csv(client, provider, period_start: str):
    return client.get(f"/providers/{provider.id}/statements/{period_start}.csv")


def rows_of(response) -> list[list[str]]:
    return list(csv.reader(io.StringIO(response.text)))


def test_csv_download_headers(client, make_provider, make_appointment):
    provider = make_provider()
    make_appointment(provider, "2026-10-06 10:00")

    response = get_csv(client, provider, "2026-10-01")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    disposition = response.headers["content-disposition"]
    assert disposition.startswith("attachment")
    assert "statement-2026-10-01.csv" in disposition


def test_csv_rows_sessions_adjustments_and_total(client, make_provider, make_appointment, make_adjustment):
    provider = make_provider()
    make_appointment(provider, "2026-10-09 10:00", client_name="Brooks, Tamara", cpt_code="90834")
    make_appointment(provider, "2026-10-02 11:00", client_name="Nguyen, Linh")
    make_appointment(provider, "2026-10-07 09:00", client_name="Okoro, Chidi", status=SessionStatus.LATE_CANCEL)
    make_appointment(provider, "2026-10-08 09:00", client_name="Gone, Not", status=SessionStatus.NO_SHOW)
    make_adjustment(provider, date(2026, 10, 5), -3500, "Claim correction: rebilled as 90834")

    rows = rows_of(get_csv(client, provider, "2026-10-01"))

    assert rows[0] == HEADER
    assert rows[1:] == [
        ["2026-10-02", "Nguyen, Linh", "90837", "Aetna", "Session", "", "165.00"],
        ["2026-10-05", "", "", "", "Adjustment", "Claim correction: rebilled as 90834", "-35.00"],
        ["2026-10-07", "Okoro, Chidi", "90837", "Aetna", "Late cancel", "", f"{LATE_CANCEL_FEE / 100:.2f}"],
        ["2026-10-09", "Brooks, Tamara", "90834", "Aetna", "Session", "", "130.00"],
        ["", "", "", "", "Total", "", "335.00"],
    ]


def test_csv_quotes_values_with_commas(client, make_provider, make_appointment):
    provider = make_provider()
    make_appointment(provider, "2026-10-02 11:00", client_name="Nguyen, Linh")

    text = get_csv(client, provider, "2026-10-01").text

    assert '"Nguyen, Linh"' in text  # a naive ",".join() would split this into two columns


def test_csv_same_day_session_comes_before_adjustment(client, make_provider, make_appointment, make_adjustment):
    provider = make_provider()
    make_adjustment(provider, date(2026, 10, 20), 2500, "Stipend")
    make_appointment(provider, "2026-10-20 16:00")

    rows = rows_of(get_csv(client, provider, "2026-10-16"))

    assert [r[4] for r in rows[1:]] == ["Session", "Adjustment", "Total"]
    assert rows[-1][-1] == "190.00"


def test_csv_for_unknown_period_start_is_rejected(client, make_provider):
    provider = make_provider()
    assert get_csv(client, provider, "2026-10-03").status_code == 422
    assert client.get("/providers/9999/statements/2026-10-01.csv").status_code == 404
