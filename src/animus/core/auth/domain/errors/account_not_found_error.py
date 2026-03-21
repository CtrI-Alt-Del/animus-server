from animus.core.shared.domain.errors import NotFoundError


class AccountNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__('Conta nao encontrada')
