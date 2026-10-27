# Payouts — provider payments service

Acme Health pays therapists ("providers") for the sessions they see, whether the client pays with
insurance or out of pocket. This repo is a simplified slice of that system: a **FastAPI + SQLAlchemy
API** that builds providers' **pay statements**, and the **provider portal** (React + TypeScript)
where providers check what they'll be paid.

## Codebase tour

```
backend/workspace/payouts/          the API (port 8713, Swagger: http://127.0.0.1:8713/docs)
  main.py                 app wiring: routers, error handlers, startup seed
  db.py                   engine/session + get_db dependency (SQLite: backend/data/payouts.db)
  timeutil.py             timezone helpers -- READ THIS FIRST
  errors.py               domain exceptions -> {"error": {"code", "message"}} responses
  models.py               ORM: Provider, FeeSchedule, Appointment, Adjustment
  schemas.py              Pydantic response models (the contract the portal relies on)
  business_calendar.py    Acme Health bank holidays
  clock.py                get_now dependency (not used much yet)
  repositories/           query helpers (providers + fee tables, appointments, adjustments)
  services/
    periods.py            pay periods (1st-15th, 16th-end of month)
    rates.py              what one appointment pays (fee schedule, late-cancel fee)
    statements.py         builds a statement for a period + the list of periods
  routers/                HTTP endpoints (providers, statements)
  seed.py                 demo data (3 providers in 3 timezones, Sep-Nov 2026)

frontend/src/payouts/               the provider portal (open it: http://127.0.0.1:5173/payouts.html)
  PortalApp.tsx           the whole UI: provider picker, Payments list, statement detail
  api.ts                  typed fetch client (/payouts-api/* is proxied to :8713)
  format.ts               money/date/time display helpers
  main.tsx, portal.css    entry point and styles
```

## Domain cheat sheet

- **Session / appointment**: one therapy visit. `cpt_code` says what kind: 90791 intake, 90834
  45-minute therapy, 90837 60-minute therapy.
- **Payer**: who's billed (Aetna, Cigna, Optum, or Self-pay).
- **Fee schedule**: the rate Acme Health has contracted to pay a provider per (payer, CPT code). Acme Health
  pays that rate on the provider's schedule regardless of when insurance actually pays Acme Health.
- **Status**: `completed` pays the contracted rate; `late_cancel` (cancelled < 24h ahead) pays the
  provider's late-cancel fee; `no_show` and `cancelled` pay nothing.
- **Adjustment**: a manual correction by Finance. Negative ones are *clawbacks* (e.g. a payer audit
  recouped money). It lands in the period containing its `effective_date`.

## Pay periods (Finance policy)

- Semi-monthly: the **1st–15th** and the **16th–last day of the month**.
- Periods are **days on the provider's own calendar**, in their timezone (`Provider.timezone`).
  A session belongs to the period containing its local date of service.
- Statements are addressed by the period's first day: `GET /providers/{id}/statements/2026-10-01`.

## Conventions (reviewers will look)

- **Money is integer cents** in the backend. Format it only for display.
- **Datetimes in the DB are naive UTC.** Convert at the edges with `timeutil.to_db` / `from_db`.
  Never compare naive with aware datetimes.
- Business rules live in `services/`, queries in `repositories/`, HTTP concerns in `routers/`.
- Raise the domain errors from `errors.py`, not `HTTPException`.

## Running and testing

- `npm run dev` starts everything (the API reloads on save; the portal hot-reloads).
- Backend tests: `uv run pytest backend/tests/payouts -q`
- Frontend tests: `npm test --prefix frontend -- tests/payouts`
- Reset the demo data: delete `backend/data/payouts.db` and save any backend file.
