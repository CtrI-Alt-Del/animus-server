from typing import Any, Literal, cast

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.example'),
        extra='ignore',
        env_file_encoding='utf-8',
    )

    MODE: Literal['dev', 'stg', 'prod']
    HOST: str = '0.0.0.0'  # noqa: S104
    PORT: int = cast('int', 8080)

    DATABASE_URL: str

    GCS_BUCKET_NAME: str
    GCS_EMULATOR_HOST: str | None = None

    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_STORAGE_BUCKET: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRATION_SECONDS: int
    JWT_REFRESH_TOKEN_EXPIRATION_SECONDS: int

    REDIS_URL: str

    INNGEST_SIGNING_KEY: str
    INNGEST_EVENT_KEY: str

    RESEND_API_KEY: str
    RESEND_SENDER_EMAIL: str

    ONESIGNAL_APP_ID: str
    ONESIGNAL_REST_API_KEY: str

    GOOGLE_CLIENT_ID: str
    PANGEA_SERVICE_URL: str

    QDRANT_URL: str
    QDRANT_API_KEY: str

    GEMINI_API_KEY: str
    OPENAI_API_KEY: str

    EMAIL_VERIFICATION_OTP_TTL_SECONDS: int
    RESET_PASSWORD_OTP_TTL_SECONDS: int
    RESET_PASSWORD_OTP_RESEND_COOLDOWN_SECONDS: int
    RESET_PASSWORD_CONTEXT_TTL_SECONDS: int

    @field_validator('GCS_EMULATOR_HOST')
    @classmethod
    def validate_gcs_emulator_host(cls, value: str, info: Any) -> str:
        mode = str(info.data.get('MODE', 'dev'))

        if value and mode != 'dev':
            msg = 'GCS_EMULATOR_HOST can only be used when MODE is dev'
            raise ValueError(msg)

        return value


Env = _Env()  # pyright: ignore[reportCallIssue]
