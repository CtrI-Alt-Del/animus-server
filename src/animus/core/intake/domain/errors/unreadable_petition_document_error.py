from animus.core.shared.domain.errors import ValidationError


class UnreadablePetitionDocumentError(ValidationError):
    def __init__(self) -> None:
        super().__init__('Documento da peticao ilegivel')
