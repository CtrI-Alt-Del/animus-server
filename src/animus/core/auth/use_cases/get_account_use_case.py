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
            raise AccountNotFoundError

        if account.is_active.is_false:
            raise AccountInactiveError

        dto = account.dto
        dto.password = None
        return dto
