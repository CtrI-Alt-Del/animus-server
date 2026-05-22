from animus.core.shared.domain.errors import NotFoundError


class AnalysisPrecedentsUnavailableError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Precedentes da analise indisponiveis')
