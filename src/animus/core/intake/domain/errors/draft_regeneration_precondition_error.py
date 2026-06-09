from animus.core.shared.domain.errors import AppError


class DraftRegenerationPreconditionError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Pre-condição de regeração de minuta invalida', message)
