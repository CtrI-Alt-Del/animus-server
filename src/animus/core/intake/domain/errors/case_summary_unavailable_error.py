from animus.core.shared.domain.errors import NotFoundError


class CaseSummaryUnavailableError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Resumo do caso indisponivel')
