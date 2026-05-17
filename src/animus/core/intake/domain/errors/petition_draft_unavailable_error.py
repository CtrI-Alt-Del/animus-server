from animus.core.shared.domain.errors import NotFoundError


class PetitionDraftUnavailableError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Minuta da petição indisponivel')
