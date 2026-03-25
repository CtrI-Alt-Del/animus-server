from animus.core.shared.domain.errors import ForbiddenError


class AccountInactiveError(ForbiddenError):
    def __init__(self) -> None:
        super().__init__('Conta desativada')
