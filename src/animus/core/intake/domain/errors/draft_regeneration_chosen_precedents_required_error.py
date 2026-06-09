from .draft_regeneration_precondition_error import DraftRegenerationPreconditionError


class DraftRegenerationChosenPrecedentsRequiredError(
    DraftRegenerationPreconditionError
):
    def __init__(self) -> None:
        super().__init__(
            'Pelo menos um precedente escolhido e obrigatorio para regeração'
        )
