from animus.core.shared.domain.errors import NotFoundError


class SecondInstanceDecisionNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Decisao da analise de segunda instancia nao encontrada')
