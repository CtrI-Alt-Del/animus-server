from animus.core.shared.domain.errors import NotFoundError


class AnalysisDocumentNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Documento da analise nao encontrado no storage')
