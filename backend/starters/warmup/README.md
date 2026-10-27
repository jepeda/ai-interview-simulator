# Warmup — patient balances

A small slice of Acme Health's billing: what each client still owes a provider's practice after their
insurance processed a session (their copay or coinsurance), minus what they've already paid.

## Codebase tour

```
backend/workspace/warmup/           the API (port 8717, Swagger: http://127.0.0.1:8717/docs)
  main.py                 app wiring
  data.py                 in-memory demo data (one provider's invoices) -- read-only here
  errors.py               domain errors -> {"error": {"code", "message"}}
  money.py                cents helpers
  services/balances.py    builds the outstanding-balances report
  routers/balances.py     GET /providers, GET /providers/{id}/balances

frontend/src/warmup/                the billing page (http://127.0.0.1:5173/warmup.html)
  BalancesApp.tsx         the UI
  api.ts                  fetch client (/warmup-api/* is proxied to :8717)
  balances.ts             view helpers (sorting, labels)
  format.ts               money/date display helpers
```

## Domain cheat sheet

- **Allowed amount**: what the insurer agreed the session is worth (cents).
- **Patient responsibility**: what the client owes for the session. Either a flat **copay**
  (`copay_cents`), or **coinsurance**: a percentage of the allowed amount (`coinsurance_pct`).
  Coinsurance is rounded to the nearest cent, **half a cent rounds up** (Finance policy).
- **Balance** = patient responsibility - amount the client has paid.
- Invoice **status**: `open` (still collecting), `paid`, `written_off` (we stopped collecting).
  The report lists `open` invoices with a balance above zero.

## Conventions

- Money is **integer cents** everywhere in the backend; format only for display.
- Business rules live in `services/`, HTTP concerns in `routers/`. Raise errors from `errors.py`.

## Running and testing

- Backend tests: `uv run pytest backend/tests/warmup -q`
- Frontend tests: `npm test --prefix frontend -- tests/warmup`
