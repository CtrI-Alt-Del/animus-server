from animus.core.shared.domain.errors import AppError


class CourtDocumentIndexNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            'Indice dos autos nao encontrado',
            'Nao foi possivel localizar um outline utilizavel no PDF dos autos',
        )
