from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.exceptions import NotFoundError, ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message}
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(part) for part in first.get("loc", []) if part != "query")
        msg = first.get("msg", "Invalid request parameter.")
        detail = f"{loc}: {msg}" if loc else msg
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": detail})
