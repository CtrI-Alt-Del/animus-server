from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    HOST: str = '127.0.0.1'
    PORT: int = 8080
    DATABASE_URL: str = 'postgresql://animus:animus@localhost:5432/animus'

    JWT_SECRET_KEY: str = ''
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_TOKEN_EXPIRATION_SECONDS: int = 3600

    REDIS_URL: str = 'redis://localhost:6379/0'
    EMAIL_VERIFICATION_OTP_TTL_SECONDS: int = 3600

    RESEND_API_KEY: str = 're_change_this'
    RESEND_SENDER_EMAIL: str = 'onboarding@resend.dev'

    ANIMUS_SERVER_URL: str = 'http://localhost:8080'
    GOOGLE_CLIENT_ID: str = 'change_this'

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        env_file_encoding='utf-8',
    )


Env = _Env()
