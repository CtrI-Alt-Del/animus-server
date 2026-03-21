from animus.core.shared.domain.errors import ConflictError


class AccountAlreadyExistsError(ConflictError):
    def __init__(self) -> None:
        super().__init__('Ja existe uma conta com este email')
