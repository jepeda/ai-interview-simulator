# Booking service — candidate brief

You've joined the team that owns **booking**: the service patients use to find an in-network
therapist and book a telehealth session. It's a small FastAPI + SQLAlchemy app. Some of it works,
some of it is broken, and two features were stubbed out by the previous engineer.

Work through the parts **in order** (later parts build on earlier ones). Each part has its own
test file under `backend/tests/booking/`; the dashboard runs all four.

| Part | Type | Where | Tests |
|---|---|---|---|
| 1. Open slots are wrong | debug | `services/availability.py` | `test_p1_availability.py` |
| 2. Provider search | implement | `services/matching.py` | `test_p2_matching.py` |
| 3. Book an appointment | implement | `services/booking.py` → `book_appointment` | `test_p3_booking.py` |
| 4. Cancel an appointment | implement | `services/booking.py` → `cancel_appointment` | `test_p4_cancellation.py` |

Ticket details are in the docstrings of the functions you need to change. Read them carefully;
the edge cases are where the tests are.

## Codebase tour

```
booking/
  main.py              app wiring: routers, error handlers, startup seed
  db.py                engine/session + get_db dependency
  clock.py             get_now dependency (tests freeze time by overriding it)
  timeutil.py          timezone helpers -- READ THIS FIRST
  errors.py            domain exceptions -> HTTP responses (raise these, don't raise HTTPException)
  models.py            ORM: Provider, ProviderLicense, ProviderPayer, Specialty,
                       AvailabilityWindow, Patient, Appointment
  schemas.py           Pydantic request/response models
  repositories/        query helpers
  services/            business logic  <-- you'll work here
  routers/             HTTP endpoints (already done; they call the services)
  seed.py              demo data for the running app
```

## Conventions (follow them -- reviewers will look)

- **Times in the DB are naive UTC.** Convert at the edges with `timeutil.to_db` / `timeutil.from_db`.
  Never compare a naive datetime with an aware one (that raises `TypeError`).
- **"Now" comes from the `get_now` dependency**, passed into services as `now`. Never call
  `datetime.now()` inside a service -- tests can't control it.
- **Errors:** raise the domain exceptions in `errors.py`. The handler turns them into
  `{"error": {"code": ..., "message": ...}}` with the right status code.
- Keep business rules in `services/`, queries in `repositories/`, HTTP concerns in `routers/`.

## Running it

- Swagger UI: http://127.0.0.1:8712/docs (started by `npm run dev`; reloads on save)
- Tests: `uv run pytest backend/tests/booking -x -q` or the dashboard's **Run tests**
