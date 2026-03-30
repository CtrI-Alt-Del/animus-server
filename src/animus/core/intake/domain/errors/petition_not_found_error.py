from animus.core.shared.domain.errors import NotFoundError


class PetitionNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Peticao nao encontrada')
