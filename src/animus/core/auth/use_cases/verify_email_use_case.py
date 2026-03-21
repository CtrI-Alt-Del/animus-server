from animus.core.auth.domain.errors import (
    AccountNotFoundError,
    InvalidEmailVerificationTokenError,
)
from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import (
    AccountsRepository,
    EmailVerificationProvider,
    JwtProvider,
)
from animus.core.shared.domain.structures import Text


class VerifyEmailUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        email_verification_provider: EmailVerificationProvider,
        jwt_provider: JwtProvider,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._email_verification_provider = email_verification_provider
        self._jwt_provider = jwt_provider

    def execute(self, token: str) -> SessionDto:
        verification_token = Text.create(token)
        is_valid_token = self._email_verification_provider.verify_verification_token(
            verification_token
        )
        if is_valid_token.is_false:
            raise InvalidEmailVerificationTokenError

        account_email = self._email_verification_provider.decode_email_from_token(
            verification_token
        )

        try:
            account = self._accounts_repository.find_by_email(account_email)
        except AccountNotFoundError as error:
            raise InvalidEmailVerificationTokenError from error

        if account.is_verified.is_false:
            account.verify()
            self._accounts_repository.replace(account)

        self._email_verification_provider.invalidate_verification_token(
            verification_token
        )

        return self._jwt_provider.encode(Text.create(account.id.value)).dto
