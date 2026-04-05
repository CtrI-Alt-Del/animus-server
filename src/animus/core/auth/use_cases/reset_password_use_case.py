from animus.core.auth.domain.errors.account_not_found_error import AccountNotFoundError
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.hash_provider import HashProvider
from animus.core.shared.domain.structures.id import Id
from animus.core.shared.domain.structures.text import Text


class ResetPasswordUseCase:
    def __init__(
        self, accounts_repository: AccountsRepository, hash_provider: HashProvider
    ) -> None:
        self._accounts_repository = accounts_repository
        self._hash_provider = hash_provider

    def execute(self, account_id: str, new_password: str) -> None:
        account = self._accounts_repository.find_by_id(Id.create(account_id))
        if not account:
            raise AccountNotFoundError
        hashed_password = self._hash_provider.generate(Text.create(new_password))
        account.password = hashed_password
        self._accounts_repository.replace(account)
