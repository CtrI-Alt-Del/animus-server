from typing import Any, ClassVar

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    DEFAULT_EMAIL_VERIFICATION_OTP_TTL_SECONDS: ClassVar[int] = 3600
    MIN_EMAIL_VERIFICATION_OTP_TTL_SECONDS: ClassVar[int] = 60
    MAX_EMAIL_VERIFICATION_OTP_TTL_SECONDS: ClassVar[int] = 86400

    HOST: str = '127.0.0.1'
    PORT: int = 8080
    DATABASE_URL: str = 'postgresql://animus:animus@localhost:5432/animus'

    JWT_SECRET_KEY: str = ''
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_TOKEN_EXPIRATION_SECONDS: int = 3600

    REDIS_URL: str = 'redis://localhost:6379/0'
    EMAIL_VERIFICATION_OTP_TTL_SECONDS: int = DEFAULT_EMAIL_VERIFICATION_OTP_TTL_SECONDS

    RESEND_API_KEY: str = 're_change_this'
    RESEND_SENDER_EMAIL: str = 'onboarding@resend.dev'

    ANIMUS_SERVER_URL: str = 'http://localhost:8080'
    GOOGLE_CLIENT_ID: str = 'change_this'

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        env_file_encoding='utf-8',
    )

    @field_validator('EMAIL_VERIFICATION_OTP_TTL_SECONDS', mode='before')
    @classmethod
    def validate_email_verification_otp_ttl_seconds(cls, value: Any) -> int:
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            return cls.DEFAULT_EMAIL_VERIFICATION_OTP_TTL_SECONDS

        if (
            parsed_value < cls.MIN_EMAIL_VERIFICATION_OTP_TTL_SECONDS
            or parsed_value > cls.MAX_EMAIL_VERIFICATION_OTP_TTL_SECONDS
        ):
            return cls.DEFAULT_EMAIL_VERIFICATION_OTP_TTL_SECONDS

        return parsed_value


Env = _Env()
