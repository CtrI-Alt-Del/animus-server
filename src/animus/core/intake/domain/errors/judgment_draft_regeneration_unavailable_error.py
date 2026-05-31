from .draft_regeneration_precondition_error import DraftRegenerationPreconditionError


class SecondInstanceJudgmentDraftRegenerationUnavailableError(
    DraftRegenerationPreconditionError
):
    def __init__(self) -> None:
        super().__init__('Nao ha minuta de sentenca persistida para regeracao')
