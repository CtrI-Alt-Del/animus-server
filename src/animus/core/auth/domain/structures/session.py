from animus.core.auth.domain.structures.dtos.session_dto import SessionDto
from animus.core.auth.domain.structures.token import Token
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


@structure
class Session(Structure):
    access_token: Token
    refresh_token: Token

    @classmethod
    def create(cls, dto: SessionDto) -> 'Session':
        return cls(
            access_token=Token.create(
                value=dto.access_token.value,
                expires_at=dto.access_token.expires_at,
            ),
            refresh_token=Token.create(
                value=dto.refresh_token.value,
                expires_at=dto.refresh_token.expires_at,
            ),
        )

    @property
    def dto(self) -> SessionDto:
        return SessionDto(
            access_token=self.access_token.dto,
            refresh_token=self.refresh_token.dto,
        )
