from animus.core.shared.domain.errors import AuthError


class InvalidEmailVerificationTokenError(AuthError):
    def __init__(self) -> None:
        super().__init__('Codigo OTP de verificação de email invalido ou expirado')
