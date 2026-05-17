from animus.core.shared.domain.errors import NotFoundError


class SecondInstanceJudgmentDraftUnavailableError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Minuta do julgamento indisponivel')
