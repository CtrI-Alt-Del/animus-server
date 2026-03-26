from pydantic_settings import BaseSettings, SettingsConfigDict


class _Env(BaseSettings):
    HOST: str = '127.0.0.1'
    PORT: int = 8080
    DATABASE_URL: str = 'postgresql://animus:animus@localhost:5432/animus'

    JWT_SECRET_KEY: str = ''
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_TOKEN_EXPIRATION_SECONDS: int = 3600

    EMAIL_VERIFICATION_SECRET_KEY: str = ''
    EMAIL_VERIFICATION_SALT: str = 'email-verification'
    EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS: int = 3600

    RESEND_API_KEY: str = 're_change_this'
    RESEND_SENDER_EMAIL: str = 'onboarding@resend.dev'

    ANIMUS_SERVER_URL: str = 'http://localhost:8080'
    GOOGLE_CLIENT_ID: str = 'change_this'
    PANGEA_SERVICE_URL: str ='https://pangeabnp.pdpj.jus.br'
    EMBEDDING_AI_MODEL:str ='models/text-embedding-004'

    VERTEX_AI_PROJECT:str =''
    VERTEX_AI_LOCATION:str =''
    VERTEX_AI_INDEX_ENDPOINT_ID:str =''
    VERTEX_AI_DEPLOY_INDEX_ID:str =''

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        env_file_encoding='utf-8',
    )


Env = _Env()
