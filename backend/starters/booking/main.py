"""Booking API. Run with `npm run dev` (port 8712). Swagger UI: http://127.0.0.1:8712/docs"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from booking.db import DB_PATH, Base, SessionLocal, engine
from booking.errors import register_error_handlers
from booking.routers import appointments, providers
from booking.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Booking API (project exercise)", lifespan=lifespan)
register_error_handlers(app)
app.include_router(providers.router)
app.include_router(appointments.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
