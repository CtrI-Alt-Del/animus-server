from animus.core.shared.domain.errors import AppError


class DraftRegenerationPreconditionError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__('Pre-condicao de regeracao de minuta invalida', message)
