from .app_error import AppError


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Erro de conflito', message)
