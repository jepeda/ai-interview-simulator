"""Sandbox API. Run with `npm run dev` (port 8716). Swagger UI: http://127.0.0.1:8716/docs"""

from fastapi import FastAPI

from sandbox.errors import register_error_handlers
from sandbox.routers import week

app = FastAPI(title="Sandbox API (mock interview demo)")
register_error_handlers(app)
app.include_router(week.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
