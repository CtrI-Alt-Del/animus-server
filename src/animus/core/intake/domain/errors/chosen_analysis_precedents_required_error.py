from animus.core.shared.domain.errors import ConflictError


class ChosenAnalysisPrecedentsRequiredError(ConflictError):
    def __init__(self) -> None:
        super().__init__('Pelo menos um precedente escolhido e obrigatorio')
