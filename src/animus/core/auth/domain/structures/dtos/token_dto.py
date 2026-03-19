from animus.core.shared.domain.decorators import dto


@dto
class TokenDto:
    value: str
    expires_at: str
