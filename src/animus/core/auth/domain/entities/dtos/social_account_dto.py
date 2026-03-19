from animus.core.shared.domain.decorators import dto


@dto
class SocialAccountDto:
    name: str
    email: str
    provider: str
    id: str | None = None
