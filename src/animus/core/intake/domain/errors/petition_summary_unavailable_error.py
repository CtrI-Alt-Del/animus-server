from animus.core.shared.domain.errors import ConflictError


class PetitionSummaryUnavailableError(ConflictError):
    def __init__(self) -> None:
        super().__init__('Resumo da peticao indisponivel para buscar precedentes')
