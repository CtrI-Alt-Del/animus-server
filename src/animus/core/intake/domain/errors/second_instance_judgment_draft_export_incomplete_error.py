from animus.core.shared.domain.errors import ValidationError


class SecondInstanceJudgmentDraftExportIncompleteError(ValidationError):
    def __init__(self, missing_fields: list[str]) -> None:
        missing_fields_text = ', '.join(missing_fields)
        super().__init__(
            'Nao e possivel exportar a minuta de sentenca. Campos obrigatorios '
            f'ausentes ou invalidos: {missing_fields_text}',
        )
