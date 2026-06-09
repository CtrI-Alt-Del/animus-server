from .draft_regeneration_precondition_error import DraftRegenerationPreconditionError


class PetitionDraftRegenerationUnavailableError(DraftRegenerationPreconditionError):
    def __init__(self) -> None:
        super().__init__('Nao ha minuta de petição persistida para regeração')
