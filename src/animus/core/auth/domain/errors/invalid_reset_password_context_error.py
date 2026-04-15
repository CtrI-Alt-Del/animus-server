from animus.core.shared.domain.errors import AuthError


class InvalidResetPasswordContextError(AuthError):
    def __init__(self) -> None:
        super().__init__('Contexto de reset de senha invalido ou expirado')
