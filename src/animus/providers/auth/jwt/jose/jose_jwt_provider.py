from datetime import UTC, datetime, timedelta

from jose import jwt

from animus.constants import Env
from animus.core.auth.domain.structures import Session
from animus.core.auth.domain.structures.dtos import SessionDto, TokenDto
from animus.core.auth.interfaces import JwtProvider
from animus.core.shared.domain.structures import Text


class JoseJwtProvider(JwtProvider):
    def encode(self, subject: Text) -> Session:
        now = datetime.now(UTC)

        access_token_expires_at = now + timedelta(
            seconds=Env.JWT_ACCESS_TOKEN_EXPIRATION_SECONDS
        )
        refresh_token_expires_at = now + timedelta(
            seconds=Env.JWT_REFRESH_TOKEN_EXPIRATION_SECONDS
        )

        access_token_value = jwt.encode(
            {
                'sub': subject.value,
                'type': 'access',
                'iat': now,
                'exp': access_token_expires_at,
            },
            Env.JWT_SECRET_KEY,
            algorithm=Env.JWT_ALGORITHM,
        )
        refresh_token_value = jwt.encode(
            {
                'sub': subject.value,
                'type': 'refresh',
                'iat': now,
                'exp': refresh_token_expires_at,
            },
            Env.JWT_SECRET_KEY,
            algorithm=Env.JWT_ALGORITHM,
        )

        return Session.create(
            SessionDto(
                access_token=TokenDto(
                    value=access_token_value,
                    expires_at=access_token_expires_at.isoformat(),
                ),
                refresh_token=TokenDto(
                    value=refresh_token_value,
                    expires_at=refresh_token_expires_at.isoformat(),
                ),
            )
        )

    def decode(self, token: Text) -> dict[str, str]:
        decoded_token = jwt.decode(
            token.value,
            Env.JWT_SECRET_KEY,
            algorithms=[Env.JWT_ALGORITHM],
        )
        return {str(key): str(value) for key, value in decoded_token.items()}
