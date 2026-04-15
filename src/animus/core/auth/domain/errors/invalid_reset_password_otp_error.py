from animus.core.shared.domain.errors import AuthError


class InvalidResetPasswordOtpError(AuthError):
    def __init__(self) -> None:
        super().__init__('Codigo OTP de reset de senha invalido ou expirado')
