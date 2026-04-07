from animus.constants.env import Env
from animus.core.auth.interfaces import (
    HashProvider,
    JwtProvider,
)
from animus.core.auth.interfaces.email_verification_provider import (
    EmailVerificationProvider,
)
from animus.core.notification.interfaces import EmailSenderProvider
from animus.core.shared.interfaces import CacheProvider, OtpProvider
from animus.core.storage.interfaces import (
    DocxProvider,
    FileStorageProvider,
    PdfProvider,
)
from animus.providers.auth.email_verification.itsdangerous_email_provider import (
    ItsdangerousEmailVerificationProvider,
)
from animus.providers.auth.hash.argon2id_hash_provider import Argon2idHashProvider
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from animus.providers.auth.otp.secrets.secrets_otp_provider import SecretsOtpProvider
from animus.providers.auth.google.google_oauth_provider import GoogleOAuthProvider
from animus.providers.notification.email_sender.resend.resend_email_sender_provider import (
    ResendEmailSenderProvider,
)
from animus.providers.shared.cache.redis.redis_cache_provider import RedisCacheProvider
from animus.providers.storage.document.docx.python_docx_provider import (
    PythonDocxProvider,
)
from animus.providers.storage.document.pdf.pypdf_pdf_provider import PypdfPdfProvider
from animus.providers.storage.file_storage.supabase.supabase_file_storage_provider import (
    SupabaseFileStorageProvider,
)


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

    @staticmethod
    def get_file_storage_provider() -> FileStorageProvider:
        return SupabaseFileStorageProvider()

    @staticmethod
    def get_pdf_provider() -> PdfProvider:
        return PypdfPdfProvider()

    @staticmethod
    def get_docx_provider() -> DocxProvider:
        return PythonDocxProvider()

    @staticmethod
    def get_email_verification_provider() -> EmailVerificationProvider:
        return ItsdangerousEmailVerificationProvider()
