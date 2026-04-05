from animus.core.auth.domain.errors.invalid_email_verification_token_error import (
    InvalidEmailVerificationTokenError,
)
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.email_verification_provider import (
    EmailVerificationProvider,
)
from animus.core.shared.domain.structures.text import Text


class VerifyResetTokenUseCase:
    def __init__(
        self,
        email_verification_provider: EmailVerificationProvider,
        accounts_repository: AccountsRepository,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._email_verification_provider = email_verification_provider

    def execute(self, token: str) -> str:
        is_valid = self._email_verification_provider.verify_verification_token(
            Text.create(token)
        )
        if not is_valid.value:
            raise InvalidEmailVerificationTokenError
        email = self._email_verification_provider.decode_email_from_token(
            Text.create(token)
        )
        account = self._accounts_repository.find_by_email(email)
        if not account:
            raise InvalidEmailVerificationTokenError
        return account.id.value
