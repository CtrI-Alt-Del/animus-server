from animus.core.shared.domain.errors import NotFoundError


class PetitionSummaryUnavailableError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Resumo da peticao indisponivel para buscar precedentes')
