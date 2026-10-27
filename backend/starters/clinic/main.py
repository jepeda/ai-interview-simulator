"""Clinic API entry point.

Run (from the repo root):  npm run dev:clinic
Docs (Swagger UI):         http://127.0.0.1:8711/docs
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from clinic.db import DB_PATH, Base, SessionLocal, engine
from clinic.routers import patients, plans
from clinic.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runs once at startup (like an Express app.listen callback), before serving requests.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Clinic API (debugging exercises)", lifespan=lifespan)
app.include_router(patients.router)
app.include_router(plans.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
