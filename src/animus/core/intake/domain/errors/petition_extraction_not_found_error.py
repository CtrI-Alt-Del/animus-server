from animus.core.shared.domain.errors import AppError


class PetitionExtractionNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            'Peticao inicial nao encontrada',
            'Nao foi possivel identificar a petição inicial nos autos da analise',
        )
