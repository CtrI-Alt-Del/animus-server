from animus.core.shared.domain.decorators import dto
from animus.core.auth.domain.structures.dtos.token_dto import TokenDto


@dto
class SessionDto:
    access_token: TokenDto
    refresh_token: TokenDto
