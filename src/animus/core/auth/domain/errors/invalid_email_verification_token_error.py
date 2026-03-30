from animus.core.shared.domain.errors import AuthError


class InvalidEmailVerificationTokenError(AuthError):
    def __init__(self) -> None:
        super().__init__('Codigo OTP de verificacao de email invalido ou expirado')
