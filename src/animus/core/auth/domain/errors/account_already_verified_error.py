from animus.core.shared.domain.errors import ConflictError


class AccountAlreadyVerifiedError(ConflictError):
    def __init__(self) -> None:
        super().__init__('Conta ja verificada')
