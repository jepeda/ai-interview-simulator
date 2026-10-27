"""Domain errors -> HTTP responses: {"error": {"code": "<code>", "message": "<message>"}}."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = 400
    code = "domain_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFound(DomainError):
    status_code = 404
    code = "not_found"


class InvalidRequest(DomainError):
    status_code = 422
    code = "invalid_request"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})
