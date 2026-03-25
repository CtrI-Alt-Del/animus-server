from animus.core.auth.domain.errors import AccountNotFoundError
from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.domain.entities.account import Account
from animus.core.auth.domain.entities.dtos.account_dto import AccountDto
from animus.core.auth.domain.entities.dtos.social_account_dto import SocialAccountDto
from animus.core.auth.domain.entities.social_account import SocialAccount
from animus.core.auth.domain.structures.social_account_provider import (
    SocialAccountProviderValue,
)
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.jwt_provider import JwtProvider
from animus.core.auth.interfaces.oauth_provider import OAuthProvider
from animus.core.shared.domain.structures.text import Text


class SignInWithGoogleUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        jwt_provider: JwtProvider,
        google_oauth_provider: OAuthProvider,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._jwt_provider = jwt_provider
        self._google_oauth_provider = google_oauth_provider

    def execute(self, id_token: str) -> SessionDto:
        name, email = self._google_oauth_provider.get_user_info(Text.create(id_token))

        try:
            account = self._accounts_repository.find_by_email(email)
        except AccountNotFoundError:
            account = None

        if not account:
            account = Account.create(
                AccountDto(
                    name=name.value,
                    email=email.value,
                    password=None,
                    is_verified=True,
                )
            )
            social_account = SocialAccount.create(
                SocialAccountDto(
                    provider='GOOGLE',
                    name=account.name.value,
                    email=account.email.value,
                )
            )
            account.add_social_account(social_account)
            self._accounts_repository.add(account, None)
        else:
            social_account = SocialAccount.create(
                SocialAccountDto(
                    name=account.name.value,
                    email=account.email.value,
                    provider=SocialAccountProviderValue.GOOGLE,
                )
            )
            if social_account not in account.social_accounts:
                account.add_social_account(social_account)
                self._accounts_repository.replace(account)

        token_dto = self._jwt_provider.encode(Text.create(account.id.value))
        return token_dto.dto
