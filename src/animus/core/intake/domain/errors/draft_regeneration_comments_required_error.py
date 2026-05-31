from .draft_regeneration_precondition_error import DraftRegenerationPreconditionError


class DraftRegenerationCommentsRequiredError(DraftRegenerationPreconditionError):
    def __init__(self) -> None:
        super().__init__('Comentarios de regeracao sao obrigatorios')
