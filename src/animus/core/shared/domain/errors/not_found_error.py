from animus.core.shared.domain.errors.app_error import AppError


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Not Found Error', message)
