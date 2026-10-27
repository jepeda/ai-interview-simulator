# Remits — claims & remittance posting

Acme Health bills insurers ("payers") for every session its therapists ("providers") see. Payers answer
with **remittances**: a payment (EFT or check) plus an **ERA / 835 file** explaining, claim by claim,
what they paid and why the rest wasn't paid. This repo is a simplified slice of the system the
**revenue-cycle team** uses: a **FastAPI + SQLAlchemy API** that posts ERAs to claims, and the
**claims portal** (React + TypeScript) where billing specialists work claims and reconcile payments.

## Codebase tour

```
backend/workspace/remits/           the API (port 8714, Swagger: http://127.0.0.1:8714/docs)
  main.py                 app wiring: routers, error handlers, startup seed
  db.py                   engine/session + get_db dependency (SQLite: backend/data/remits.db)
  models.py               ORM: Provider, FeeSchedule, Claim, Remittance, ClaimPayment,
                          PaymentAdjustment, RemitAdjustment (diagram at the top)
  schemas.py              Pydantic models: the inbound ERA payload + the API the portal relies on
  money.py                dollars <-> cents
  carc.py                 adjustment group/reason codes (CO-45, PR-3...), claim status codes
  errors.py               domain exceptions -> {"error": {"code", "message"}} responses
  timeutil.py, clock.py   UTC helpers; get_now / get_today dependencies (override in tests)
  repositories/           queries (claims, remittances, fee schedules)
  services/
    posting.py            cash posting: apply an incoming ERA to our claims
    claims.py             claim balance + status
    remittances.py        remittance summaries: payment total vs what we posted
  routers/                HTTP endpoints (claims, remittances)
  seed.py                 demo data: 24 claims, and the ERA files we received in Oct 2026,
                          replayed through posting.py in the order they arrived

frontend/src/remits/                the claims portal (open it: http://127.0.0.1:5173/remits.html)
  ClaimsApp.tsx           the whole UI: Claims tab (list + detail), Remittances tab (list + detail)
  api.ts                  typed fetch client (/remits-api/* is proxied to :8714)
  format.ts               money/date display helpers
  main.tsx, portal.css    entry point and styles
```

## Domain cheat sheet

- **Claim**: one session billed to one payer, identified by our claim number (`HW-1042`). We bill
  our **chargemaster** price (`billed`), which is always more than the payer will pay.
- **CPT code**: what was billed. 90791 intake, 90834 45-minute therapy, 90837 60-minute therapy.
- **Fee schedule / allowed amount**: what our contract with the payer allows for a CPT code. The
  allowed amount is split between the payer (**paid**) and the client (**patient responsibility**).
- **Remittance / ERA / 835**: the payer's payment and its explanation. One remittance pays many
  claims. Amounts arrive as **dollar strings** (`"137.17"`).
- **Trace number** (TRN02): the EFT trace or check number of the payment. Together with the payer it
  identifies one payment. Clearinghouses deliver ERAs to us over a queue and sometimes deliver the
  same file again (retries, outages).
- **Adjustments (CAS)**: every billed dollar that wasn't paid is explained by a **group code** +
  **reason code (CARC)**:
  - `CO` contractual obligation: written off, never billed to the client. `CO-45` = "above the
    contracted rate" (the normal one). Others like `CO-197` (no prior authorization), `CO-16`
    (missing info), `CO-29` (filed too late) are **denials**.
  - `PR` patient responsibility: `PR-1` deductible, `PR-2` coinsurance, `PR-3` copay.
  - An 835 line always balances: `billed = paid + sum(adjustments)`.
- **Claim status code** (CLP02): `1` processed as primary, `4` denied, `22` reversal (the payer takes a
  payment back: negative amounts).
- **Remit-level adjustment (PLB)**: money not tied to a claim in this file, e.g. `WO` overpayment
  recovery (recoupment of an older claim's overpayment, negative) or `L6` interest.
- **Balancing**: a remittance's `total_paid` (what hits the bank) must equal the sum of its claim
  payments plus its remit-level adjustments. Finance won't close the month with an out-of-balance
  remit.

## Claim balance and status

```
balance = billed - paid - adjusted (CO/OA/PI) - patient responsibility (PR)
```

`submitted` (nothing posted yet) · `denied` (nothing paid, denial reason) · `paid` (balance 0) ·
`partially_paid` (balance > 0) · `overpaid` (balance < 0: we owe the payer a refund).

## Conventions (reviewers will look)

- **Money is integer cents** in the backend and the API. Convert payer dollars once, at the edge.
- **Datetimes in the DB are naive UTC.** Convert with `timeutil.to_db` / `from_db`.
- Business rules live in `services/`, queries in `repositories/`, HTTP concerns in `routers/`.
- Raise the domain errors from `errors.py`, not `HTTPException`.

## Running and testing

- `npm run dev` starts everything (the API reloads on save; the portal hot-reloads).
- Backend tests: `uv run pytest backend/tests/remits -q`
- Frontend tests: `npm test --prefix frontend -- tests/remits`
- Post an ERA by hand: `POST /remittances` in Swagger (the request body has an example shape).
- Reset the demo data: **⟲ Reset demo data** in the interview's App tab (or stop the API, delete
  `backend/data/remits.db` and start it again). The seed replays every ERA through the posting code,
  so it picks up your changes.
