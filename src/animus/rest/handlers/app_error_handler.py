from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from animus.core.shared.domain.errors import (
    AppError,
    AuthError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


class AppErrorHandler:
    @staticmethod
    def _build_response(status_code: int, error: Exception) -> JSONResponse:
        if isinstance(error, AppError):
            return JSONResponse(
                status_code=status_code,
                content={
                    'title': error.title,
                    'message': error.message,
                },
            )

        return JSONResponse(
            status_code=status_code,
            content={
                'title': 'Application Error',
                'message': str(error),
            },
        )

    @staticmethod
    async def handle_conflict_error(_: Request, error: Exception) -> JSONResponse:
        return AppErrorHandler._build_response(409, error)

    @staticmethod
    async def handle_not_found_error(_: Request, error: Exception) -> JSONResponse:
        return AppErrorHandler._build_response(404, error)

    @staticmethod
    async def handle_validation_error(_: Request, error: Exception) -> JSONResponse:
        return AppErrorHandler._build_response(400, error)

    @staticmethod
    async def handle_auth_error(_: Request, error: Exception) -> JSONResponse:
        return AppErrorHandler._build_response(401, error)

    @staticmethod
    async def handle_forbidden_error(_: Request, error: Exception) -> JSONResponse:
        return AppErrorHandler._build_response(403, error)

    @staticmethod
    async def handle_app_error(_: Request, error: Exception) -> JSONResponse:
        return AppErrorHandler._build_response(400, error)

    @staticmethod
    def register(app: FastAPI) -> None:
        app.add_exception_handler(ConflictError, AppErrorHandler.handle_conflict_error)
        app.add_exception_handler(NotFoundError, AppErrorHandler.handle_not_found_error)
        app.add_exception_handler(
            ValidationError, AppErrorHandler.handle_validation_error
        )
        app.add_exception_handler(AuthError, AppErrorHandler.handle_auth_error)
        app.add_exception_handler(
            ForbiddenError, AppErrorHandler.handle_forbidden_error
        )
        app.add_exception_handler(AppError, AppErrorHandler.handle_app_error)
