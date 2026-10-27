"""Warmup API. Run with `npm run dev` (port 8717). Swagger UI: http://127.0.0.1:8717/docs"""

from fastapi import FastAPI

from warmup.errors import register_error_handlers
from warmup.routers import balances

app = FastAPI(title="Patient balances API (warmup)")
register_error_handlers(app)
app.include_router(balances.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
