from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.errors import (
    AccountNotFoundError,
    InvalidEmailVerificationTokenError,
)
from animus.core.auth.domain.structures import Email, Otp
from animus.core.auth.domain.structures.dtos import SessionDto
from animus.core.auth.interfaces import (
    AccountsRepository,
    JwtProvider,
)
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Text
from animus.core.shared.interfaces import CacheProvider


class VerifyEmailUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        cache_provider: CacheProvider,
        jwt_provider: JwtProvider,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._cache_provider = cache_provider
        self._jwt_provider = jwt_provider

    def execute(self, email: str, otp: str) -> SessionDto:
        account_email = Email.create(email)
        account_email_otp = Otp.create(otp)

        email_verification_cache_key = CacheKeys().get_email_verification(
            account_email.value
        )
        cached_account_email_otp = self._cache_provider.get(
            email_verification_cache_key
        )
        if cached_account_email_otp is None:
            raise InvalidEmailVerificationTokenError

        try:
            stored_account_email_otp = Otp.create(cached_account_email_otp.value)
        except ValidationError as error:
            raise InvalidEmailVerificationTokenError from error

        if account_email_otp != stored_account_email_otp:
            raise InvalidEmailVerificationTokenError

        try:
            account = self._accounts_repository.find_by_email(account_email)
        except AccountNotFoundError as error:
            raise InvalidEmailVerificationTokenError from error

        if account.is_verified.is_false:
            account.verify()
            self._accounts_repository.replace(account)

        self._cache_provider.delete(email_verification_cache_key)

        return self._jwt_provider.encode(Text.create(account.id.value)).dto
