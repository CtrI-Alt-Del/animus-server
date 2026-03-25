from animus.constants.env import Env
from animus.core.auth.interfaces import (
    HashProvider,
    JwtProvider,
)
from animus.core.notification.interfaces import EmailSenderProvider
from animus.core.shared.interfaces import CacheProvider, OtpProvider
from animus.providers.auth import (
    Argon2idHashProvider,
    JoseJwtProvider,
    SecretsOtpProvider,
)
from animus.providers.auth.google.google_oauth_provider import GoogleOAuthProvider
from animus.providers.notification import (
    ResendEmailSenderProvider,
)
from animus.providers.shared import RedisCacheProvider


class ProvidersPipe:
    @staticmethod
    def get_hash_provider() -> HashProvider:
        return Argon2idHashProvider()

    @staticmethod
    def get_jwt_provider() -> JwtProvider:
        return JoseJwtProvider()

    @staticmethod
    def get_cache_provider() -> CacheProvider:
        return RedisCacheProvider(redis_url=Env.REDIS_URL)

    @staticmethod
    def get_otp_provider() -> OtpProvider:
        return SecretsOtpProvider()

    @staticmethod
    def get_email_sender_provider() -> EmailSenderProvider:
        return ResendEmailSenderProvider()

    @staticmethod
    def get_google_oauth_provider() -> GoogleOAuthProvider:
        return GoogleOAuthProvider(client_id=Env.GOOGLE_CLIENT_ID)
