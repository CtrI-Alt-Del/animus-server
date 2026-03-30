from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import AccountInactiveError, AccountNotFoundError
from animus.core.auth.interfaces import AccountsRepository
from animus.core.shared.domain.structures import Id


class GetAccountUseCase:
    def __init__(self, accounts_repository: AccountsRepository) -> None:
        self._accounts_repository = accounts_repository

    def execute(self, account_id: Id) -> AccountDto:
        account = self._accounts_repository.find_by_id(account_id)

        if account is None:
            raise AccountNotFoundError()

        if not account.is_active.value:
            raise AccountInactiveError()

        return AccountDto(
            id=account.id.value if account.id else None,
            name=account.name.value,
            email=account.email.value,
            password=None,
            is_verified=account.is_verified.value,
            is_active=account.is_active.value,
            social_accounts=[
                social.dto for social in account.social_accounts
            ] if account.social_accounts else [],
        )
