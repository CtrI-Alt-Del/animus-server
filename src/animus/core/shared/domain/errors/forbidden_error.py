from .app_error import AppError


class ForbiddenError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Erro de acesso negado', message)
