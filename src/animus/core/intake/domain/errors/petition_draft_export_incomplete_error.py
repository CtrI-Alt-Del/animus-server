from animus.core.shared.domain.errors import ValidationError


class PetitionDraftExportIncompleteError(ValidationError):
    def __init__(self, missing_fields: list[str]) -> None:
        missing_fields_text = ', '.join(missing_fields)
        super().__init__(
            'Nao e possivel exportar a minuta. Campos obrigatorios ausentes ou invalidos: '
            f'{missing_fields_text}',
        )
