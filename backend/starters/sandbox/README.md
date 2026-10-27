# Sandbox — weekly earnings card

A deliberately tiny app for trying out the mock-interview screen (it doesn't count as an attempt).
Providers (therapists) see what they've earned this week; Acme Health pays them a contracted rate per
session.

## Codebase tour

```
backend/workspace/sandbox/          the API (port 8716, Swagger: http://127.0.0.1:8716/docs)
  main.py                 app wiring
  data.py                 in-memory demo data (one provider, one week) and the rate card
  errors.py               domain errors -> {"error": {"code", "message"}}
  services/earnings.py    builds the weekly earnings card
  routers/week.py         GET /providers, GET /providers/{id}/week?start=YYYY-MM-DD

frontend/src/sandbox/               the card (http://127.0.0.1:5173/sandbox.html)
  WeekApp.tsx             the UI
  api.ts                  fetch client (/sandbox-api/* is proxied to :8716)
  format.ts               money/date display helpers
```

## Domain cheat sheet

- **Session status**: `completed` pays the contracted rate for its CPT code; `late_cancel`
  (cancelled < 24h ahead) pays the flat **late-cancel fee** ($75.00); `no_show` and `cancelled`
  pay nothing and don't appear on the card.
- **CPT code**: 90791 intake, 90834 45-minute therapy, 90837 60-minute therapy.
- **Money is integer cents** in the backend; the frontend formats it for display.
- Weeks start on **Monday**.

## Running and testing

- Backend tests: `uv run pytest backend/tests/sandbox -q`
- Frontend tests: `npm test --prefix frontend -- tests/sandbox`
