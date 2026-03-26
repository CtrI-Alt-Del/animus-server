from animus.core.shared.domain.errors import NotFoundError


class PrecedentNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Precedente nao encontrado')
