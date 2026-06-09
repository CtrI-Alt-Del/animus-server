from animus.core.shared.domain.errors import AppError


class InsufficientCourtDocumentError(AppError):
    def __init__(self) -> None:
        super().__init__(
            'Pecas processuais insuficientes',
            'Nao foi possivel localizar sentenca e apelação no outline dos autos',
        )
