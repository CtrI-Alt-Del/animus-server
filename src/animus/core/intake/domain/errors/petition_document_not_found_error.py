from animus.core.shared.domain.errors import NotFoundError


class PetitionDocumentNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Documento da peticao nao encontrado no storage')
