from animus.core.shared.domain.decorators import dto


@dto
class SessionDto:
    access_token: str
    refresh_token: str
