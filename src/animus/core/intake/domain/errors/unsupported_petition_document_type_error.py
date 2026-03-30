from animus.core.shared.domain.errors import ValidationError


class UnsupportedPetitionDocumentTypeError(ValidationError):
    def __init__(self) -> None:
        super().__init__('Tipo de documento da peticao nao suportado')
