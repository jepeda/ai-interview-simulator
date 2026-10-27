# Earnings — provider rates and earnings dashboard

Acme Health contracts a **rate per session** with every provider (therapist) for each payer and type of
service, and those rates change over time. This repo is a simplified slice of that system: a
**FastAPI + SQLAlchemy API** that keeps providers' fee schedules and computes what they've earned,
and the **earnings dashboard** (React + TypeScript) where providers see their year so far and their
rate card.

## Codebase tour

```
backend/workspace/earnings/         the API (port 8715, Swagger: http://127.0.0.1:8715/docs)
  main.py                 app wiring: routers, error handlers, startup seed
  db.py                   engine/session + get_db dependency (SQLite: backend/data/earnings.db)
  clock.py                get_today dependency (Acme Health's calendar is US Eastern)
  errors.py               domain exceptions -> {"error": {"code", "message"}} responses
  models.py               ORM: Provider, ContractedRate, Appointment, Adjustment
  schemas.py              Pydantic response models (the contract the dashboard relies on)
  repositories/           query helpers (providers, rates, appointments, adjustments)
  services/
    rates.py              RateTable: the rate a session pays, looked up in memory
    rate_card.py          today's rates + scheduled changes, for the Rates tab
    earnings.py           year summary (by month, by payer) and one month's sessions
    months.py             "2026-07" month keys
  routers/                HTTP endpoints (providers, earnings, rates)
  seed.py                 demo data (3 providers, Jan-Nov 2026)

frontend/src/earnings/              the dashboard (open it: http://127.0.0.1:5173/earnings.html)
  DashboardApp.tsx        the whole UI: provider/year pickers, chart, by payer, month detail, rate card
  api.ts                  typed fetch client (/earnings-api/* is proxied to :8715)
  chart.ts                turns the API's months into the 12 bars of the chart
  format.ts               money/date display helpers
  main.tsx, dashboard.css entry point and styles
```

## Domain cheat sheet

- **Session / appointment**: one therapy visit on a `service_date`. `cpt_code` says what kind:
  90791 intake (a client's first visit), 90834 45-minute therapy, 90837 60-minute therapy.
- **Payer**: the insurer billed (Aetna, Cigna, Optum).
- **Status**: `completed` sessions earn the contracted rate; `no_show` and `cancelled` earn nothing
  here; `scheduled` sessions haven't happened yet.
- **Paid on**: Acme Health pays each week's completed sessions on the Friday of the following week,
  whether or not the payer has paid Acme Health yet. `paid_on` is null until then.
- **Adjustment**: a one-off correction by Finance (back pay, stipends, or a negative *recoupment*
  when a payer claws money back). Adjustments are on pay statements, not on this dashboard.

## Rates (Network Ops policy)

- A provider's **fee schedule** is a list of `ContractedRate` entries: from `effective_date` on,
  Acme Health pays `rate_cents` for that (payer, CPT code). An entry applies until a later entry for the
  same (payer, CPT) takes effect. There are no end dates.
- **A session is paid the rate in effect on its date of service** (`effective_date <= service_date`),
  no matter when the rate was entered. Rate increases are often entered weeks ahead of time.
- Entries are **append-only** (Finance audits them). Ops never edits an entry: to fix a mistake they
  add a **correction**, a new entry with the **same effective date**. When two entries share an
  effective date, the one entered last wins.
- `GET /providers/{id}/rates` is that audit trail, in the order the entries were entered.
- The **rate card** shows what each (payer, CPT) pays today, plus the next scheduled change.

## Conventions (reviewers will look)

- **Money is integer cents** in the backend. Format it only for display.
- Dates of service, effective dates and pay dates are plain calendar dates (`date`, "YYYY-MM-DD"
  in JSON). "Today" comes from the `get_today` dependency, never `date.today()` in a service.
- Business rules live in `services/`, queries in `repositories/`, HTTP concerns in `routers/`.
- Raise the domain errors from `errors.py`, not `HTTPException`.

## Running and testing

- `npm run dev` starts everything (the API reloads on save; the dashboard hot-reloads).
- Backend tests: `uv run pytest backend/tests/earnings -q`
- Frontend tests: `npm test --prefix frontend -- tests/earnings`
- Reset the demo data: delete `backend/data/earnings.db` and save any backend file.
