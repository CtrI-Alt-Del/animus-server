from animus.core.shared.domain.errors import ValidationError


class InconsistentAnalysisTypeError(ValidationError):
    def __init__(self) -> None:
        super().__init__('Tipo de análise incoerente')
