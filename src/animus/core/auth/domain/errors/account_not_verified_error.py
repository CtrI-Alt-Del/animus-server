from animus.core.shared.domain.errors import ForbiddenError


class AccountNotVerifiedError(ForbiddenError):
    def __init__(self) -> None:
        super().__init__('E-mail nao confirmado')
