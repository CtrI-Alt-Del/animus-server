from typing import Any, ClassVar, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    DEFAULT_EMAIL_VERIFICATION_OTP_TTL_SECONDS: ClassVar[int] = 3600
    MIN_EMAIL_VERIFICATION_OTP_TTL_SECONDS: ClassVar[int] = 60
    MAX_EMAIL_VERIFICATION_OTP_TTL_SECONDS: ClassVar[int] = 86400

    MODE: Literal['dev', 'stg', 'prod'] = 'dev'
    HOST: str = '127.0.0.1'
    PORT: int = 8080
    ANIMUS_SERVER_URL: str = 'http://localhost:8080'

    DATABASE_URL: str = 'postgresql://animus:animus@localhost:5432/animus'
    GCS_BUCKET_NAME: str = 'animus'
    STORAGE_EMULATOR_HOST: str = ''

    JWT_SECRET_KEY: str = ''
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_TOKEN_EXPIRATION_SECONDS: int = 3600

    REDIS_URL: str = 'redis://localhost:6379/0'
    EMAIL_VERIFICATION_OTP_TTL_SECONDS: int = DEFAULT_EMAIL_VERIFICATION_OTP_TTL_SECONDS

    RESEND_API_KEY: str = 'change_this'
    RESEND_SENDER_EMAIL: str = 'onboarding@resend.dev'

    GOOGLE_CLIENT_ID: str = 'change_this'
    PANGEA_SERVICE_URL: str = 'https://pangeabnp.pdpj.jus.br'

    QDRANT_URL: str = 'http://localhost:6333'
    GEMINI_API_KEY: str = 'change_this'
    OPENAI_API_KEY: str = 'change_this'

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        env_file_encoding='utf-8',
    )

    EMAIL_VERIFICATION_SECRET_KEY:str = 'change_this'
    EMAIL_VERIFICATION_SALT:str = 'change_this'
    EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS:int = 3600

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

    @field_validator('STORAGE_EMULATOR_HOST')
    @classmethod
    def validate_storage_emulator_host(cls, value: str, info: Any) -> str:
        mode = str(info.data.get('MODE', 'dev'))

        if value and mode != 'dev':
            msg = 'STORAGE_EMULATOR_HOST can only be used when MODE is dev'
            raise ValueError(msg)

        return value


Env = _Env()
