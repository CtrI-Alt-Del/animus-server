from animus.core.auth.domain.structures.dtos.session_dto import SessionDto
from animus.core.auth.domain.structures.token import Token
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure


@structure
class Session(Structure):
    access_token: Token
    refresh_token: Token

    @classmethod
    def create(cls, access_token: Token, refresh_token: Token) -> 'Session':
        return cls(access_token=access_token, refresh_token=refresh_token)

    @property
    def dto(self) -> SessionDto:
        return SessionDto(
            access_token=self.access_token.value,
            refresh_token=self.refresh_token.value,
        )
