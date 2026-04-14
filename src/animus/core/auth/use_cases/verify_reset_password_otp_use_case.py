from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.errors import InvalidResetPasswordOtpError
from animus.core.auth.domain.structures import Email, Otp
from animus.core.auth.domain.structures.dtos import ResetPasswordContextDto
from animus.core.auth.interfaces import AccountsRepository
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Text, Ttl
from animus.core.shared.interfaces import CacheProvider


class VerifyResetPasswordOtpUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        cache_provider: CacheProvider,
        reset_password_context_ttl: Ttl | None = None,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._cache_provider = cache_provider
        self._reset_password_context_ttl = (
            reset_password_context_ttl
            if reset_password_context_ttl is not None
            else Ttl.create(3600)
        )

    def execute(self, email: str, otp: str) -> ResetPasswordContextDto:
        account_email = Email.create(email)
        account_email_otp = Otp.create(otp)

        reset_password_otp_attempts_cache_key = (
            CacheKeys().get_reset_password_otp_attempts(account_email.value)
        )
        cached_remaining_attempts = self._cache_provider.get(
            reset_password_otp_attempts_cache_key
        )
        try:
            remaining_attempts = (
                int(cached_remaining_attempts.value)
                if cached_remaining_attempts is not None
                else Otp.MAX_VERIFICATION_ATTEMPTS
            )
        except ValueError as error:
            raise InvalidResetPasswordOtpError from error

        if remaining_attempts <= 0:
            raise InvalidResetPasswordOtpError

        reset_password_otp_cache_key = CacheKeys().get_reset_password_otp(
            account_email.value
        )
        cached_account_email_otp = self._cache_provider.get(
            reset_password_otp_cache_key
        )
        if cached_account_email_otp is None:
            raise InvalidResetPasswordOtpError

        try:
            stored_account_email_otp = Otp.create(cached_account_email_otp.value)
        except ValidationError as error:
            raise InvalidResetPasswordOtpError from error

        if account_email_otp != stored_account_email_otp:
            self._cache_provider.set(
                key=reset_password_otp_attempts_cache_key,
                value=Text.create(str(remaining_attempts - 1)),
            )
            raise InvalidResetPasswordOtpError

        account = self._accounts_repository.find_by_email(account_email)
        if account is None:
            raise InvalidResetPasswordOtpError

        reset_context = Id.create().value
        reset_password_context_cache_key = CacheKeys().get_reset_password_context(
            reset_context
        )
        self._cache_provider.set_with_ttl(
            key=reset_password_context_cache_key,
            value=Text.create(account.id.value),
            ttl=self._reset_password_context_ttl,
        )

        self._cache_provider.delete(reset_password_otp_cache_key)
        self._cache_provider.delete(reset_password_otp_attempts_cache_key)
        self._cache_provider.delete(
            CacheKeys().get_reset_password_otp_resend_cooldown(account_email.value)
        )

        return ResetPasswordContextDto(reset_context=reset_context)
