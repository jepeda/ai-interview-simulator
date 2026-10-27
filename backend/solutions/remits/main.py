"""Remits API (claims & remittance posting). Run with `npm run dev` (port 8714).

Swagger UI: http://127.0.0.1:8714/docs
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from remits.db import DB_PATH, Base, SessionLocal, engine
from remits.errors import register_error_handlers
from remits.routers import claims, remittances, worklists
from remits.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Remits API (AI interview)", lifespan=lifespan)
register_error_handlers(app)
app.include_router(claims.router)
app.include_router(remittances.router)
app.include_router(worklists.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
