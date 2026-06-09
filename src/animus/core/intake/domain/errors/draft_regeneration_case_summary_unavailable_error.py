from .draft_regeneration_precondition_error import DraftRegenerationPreconditionError


class DraftRegenerationCaseSummaryUnavailableError(DraftRegenerationPreconditionError):
    def __init__(self) -> None:
        super().__init__('Resumo do caso indisponivel para regeração da minuta')
