from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.errors import InvalidResetPasswordContextError
from animus.core.auth.domain.structures import Password
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.hash_provider import HashProvider
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Text
from animus.core.shared.interfaces import CacheProvider


class ResetPasswordUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        cache_provider: CacheProvider,
        hash_provider: HashProvider,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._cache_provider = cache_provider
        self._hash_provider = hash_provider

    def execute(self, reset_context: str, new_password: str) -> None:
        reset_password_context_cache_key = CacheKeys().get_reset_password_context(
            reset_context
        )
        cached_account_id = self._cache_provider.get(reset_password_context_cache_key)
        if cached_account_id is None:
            raise InvalidResetPasswordContextError

        try:
            account_id = Id.create(cached_account_id.value)
        except ValidationError as error:
            raise InvalidResetPasswordContextError from error

        account = self._accounts_repository.find_by_id(account_id)
        if not account:
            raise InvalidResetPasswordContextError

        account_password = Password.create(new_password)
        hashed_password = self._hash_provider.generate(Text.create(account_password.value))
        account.password = hashed_password
        self._accounts_repository.replace(account)
        self._cache_provider.delete(reset_password_context_cache_key)
