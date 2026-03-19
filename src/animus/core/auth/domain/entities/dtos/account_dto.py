from animus.core.auth.domain.entities.dtos.social_account_dto import SocialAccountDto
from animus.core.shared.domain.decorators import dto


@dto
class AccountDto:
    name: str
    email: str
    password: str | None
    id: str | None = None
    is_verified: bool = False
    is_active: bool = True
    social_accounts: list[SocialAccountDto] | None = None
