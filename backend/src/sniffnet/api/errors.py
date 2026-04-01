from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiException(Exception):
    def __init__(self, status_code: int, message: str, validation_errors: dict[str, str] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.validation_errors = validation_errors


class BadRequestException(ApiException):
    def __init__(self, message: str, validation_errors: dict[str, str] | None = None):
        super().__init__(status.HTTP_400_BAD_REQUEST, message, validation_errors)


class ConflictException(ApiException):
    def __init__(self, message: str):
        super().__init__(status.HTTP_409_CONFLICT, message)


class NotFoundException(ApiException):
    def __init__(self, message: str):
        super().__init__(status.HTTP_404_NOT_FOUND, message)


class IntegrationException(ApiException):
    def __init__(self, message: str):
        super().__init__(status.HTTP_502_BAD_GATEWAY, message)


def _error_body(
    request: Request,
    status_code: int,
    message: str,
    validation_errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status_code,
        "error": HTTPStatus(status_code).phrase,
        "message": message,
        "path": request.url.path,
        "validationErrors": validation_errors,
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiException)
    async def handle_api_exception(request: Request, exc: ApiException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(request, exc.status_code, exc.message, exc.validation_errors),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors: dict[str, str] = {}
        for error in exc.errors():
            loc = error.get("loc", ())
            field = ".".join(str(item) for item in loc if item not in {"body", "query", "path"}) or "request"
            errors[field] = error.get("msg", "Invalid value")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(request, status.HTTP_400_BAD_REQUEST, "Validation failed", errors),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                request,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Unexpected server error",
            ),
        )
