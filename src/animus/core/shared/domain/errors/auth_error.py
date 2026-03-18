from .app_error import AppError


class AuthError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Erro de autenticação', message)
