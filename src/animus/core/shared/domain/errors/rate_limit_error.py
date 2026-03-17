from .app_error import AppError


class RateLimitError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Erro de limite de requisições', message)
