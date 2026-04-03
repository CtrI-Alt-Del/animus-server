from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import AccountNotFoundError
from animus.core.auth.interfaces import AccountsRepository
from animus.core.shared.domain.structures import Id, Name


class UpdateAccountUseCase:
    def __init__(self, accounts_repository: AccountsRepository) -> None:
        self._accounts_repository = accounts_repository

    def execute(self, *, account_id: str, name: str) -> AccountDto:
        id_obj = Id.create(account_id)
        name_obj = Name.create(name)

        account = self._accounts_repository.find_by_id(id_obj)

        if account is None:
            raise AccountNotFoundError

        account.rename(name_obj)

        self._accounts_repository.replace(account)

        return account.dto
