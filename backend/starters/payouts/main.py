"""Payouts API. Run with `npm run dev` (port 8713). Swagger UI: http://127.0.0.1:8713/docs"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from payouts.db import DB_PATH, Base, SessionLocal, engine
from payouts.errors import register_error_handlers
from payouts.routers import providers, statements
from payouts.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Payouts API (AI interview)", lifespan=lifespan)
register_error_handlers(app)
app.include_router(providers.router)
app.include_router(statements.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
