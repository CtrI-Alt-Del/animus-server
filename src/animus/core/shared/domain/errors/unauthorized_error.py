from .app_error import AppError


class UnauthorizedError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Erro de não autorizado', message)
