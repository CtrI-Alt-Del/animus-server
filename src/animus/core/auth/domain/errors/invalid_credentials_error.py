from animus.core.shared.domain.errors import AuthError


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__('E-mail ou senha incorretos')
