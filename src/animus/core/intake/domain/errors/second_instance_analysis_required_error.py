from animus.core.shared.domain.errors import ConflictError


class SecondInstanceAnalysisRequiredError(ConflictError):
    def __init__(self) -> None:
        super().__init__('Análise de segunda instancia obrigatoria')
