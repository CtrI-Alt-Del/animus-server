from animus.core.auth.interfaces import (
    EmailVerificationProvider,
    HashProvider,
    JwtProvider,
)
from animus.core.notification.interfaces import EmailSenderProvider
from animus.providers.auth import (
    Argon2idHashProvider,
    ItsdangerousEmailVerificationProvider,
    JoseJwtProvider,
)
from animus.providers.notification import (
    ResendEmailSenderProvider,
)


class ProvidersPipe:
    @staticmethod
    def get_hash_provider() -> HashProvider:
        return Argon2idHashProvider()

    @staticmethod
    def get_jwt_provider() -> JwtProvider:
        return JoseJwtProvider()

    @staticmethod
    def get_email_verification_provider() -> EmailVerificationProvider:
        return ItsdangerousEmailVerificationProvider()

    @staticmethod
    def get_email_sender_provider() -> EmailSenderProvider:
        return ResendEmailSenderProvider()
