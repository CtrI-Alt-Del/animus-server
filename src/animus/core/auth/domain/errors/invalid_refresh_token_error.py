from animus.core.shared.domain.errors import AuthError


class InvalidRefreshTokenError(AuthError):
    def __init__(self) -> None:
        super().__init__('Refresh token invalido')
