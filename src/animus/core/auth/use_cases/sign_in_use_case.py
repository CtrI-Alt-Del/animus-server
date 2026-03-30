from animus.core.auth.domain.errors import (
    AccountInactiveError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
)
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import AccountsRepository, HashProvider, JwtProvider
from animus.core.shared.domain.structures import Text


class SignInUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        hash_provider: HashProvider,
        jwt_provider: JwtProvider,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._hash_provider = hash_provider
        self._jwt_provider = jwt_provider

    def execute(self, email: str, password: str) -> SessionDto:
        account_email = Email.create(email)
        account_password = Text.create(password)

        account = self._accounts_repository.find_by_email(account_email)
        if account is None:
            raise InvalidCredentialsError

        password_hash = self._accounts_repository.find_password_hash_by_email(
            account_email
        )

        if password_hash is None:
            raise InvalidCredentialsError

        is_valid_password = self._hash_provider.verify(account_password, password_hash)

        if is_valid_password.is_false:
            raise InvalidCredentialsError

        if account.is_verified.is_false:
            raise AccountNotVerifiedError

        if account.is_active.is_false:
            raise AccountInactiveError

        session = self._jwt_provider.encode(Text.create(account.id.value))
        return session.dto
