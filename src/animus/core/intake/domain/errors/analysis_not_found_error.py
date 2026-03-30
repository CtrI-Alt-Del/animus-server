from animus.core.shared.domain.errors import NotFoundError


class AnalysisNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Analise nao encontrada')
