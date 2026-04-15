from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.events import PasswordResetRequestEvent
from animus.core.auth.domain.structures import Email, Otp
from animus.core.auth.interfaces import AccountsRepository
from animus.core.shared.domain.structures import Text, Ttl
from animus.core.shared.interfaces import Broker, CacheProvider, OtpProvider


class ResendResetPasswordOtpUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        otp_provider: OtpProvider,
        cache_provider: CacheProvider,
        broker: Broker,
        reset_password_otp_ttl: Ttl | None = None,
        reset_password_otp_resend_cooldown_ttl: Ttl | None = None,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._otp_provider = otp_provider
        self._cache_provider = cache_provider
        self._broker = broker
        self._reset_password_otp_ttl = (
            reset_password_otp_ttl
            if reset_password_otp_ttl is not None
            else Ttl.create(3600)
        )
        self._reset_password_otp_resend_cooldown_ttl = (
            reset_password_otp_resend_cooldown_ttl
            if reset_password_otp_resend_cooldown_ttl is not None
            else Ttl.create(60)
        )

    def execute(self, email: str) -> None:
        account_email = Email.create(email)
        account = self._accounts_repository.find_by_email(account_email)
        if account is None:
            return

        reset_password_otp_resend_cooldown_cache_key = (
            CacheKeys().get_reset_password_otp_resend_cooldown(account_email.value)
        )
        cached_cooldown = self._cache_provider.get(
            reset_password_otp_resend_cooldown_cache_key
        )
        if cached_cooldown is not None:
            return

        account_email_otp = self._otp_provider.generate()
        reset_password_otp_cache_key = CacheKeys().get_reset_password_otp(
            account_email.value
        )
        reset_password_otp_attempts_cache_key = (
            CacheKeys().get_reset_password_otp_attempts(account_email.value)
        )

        self._cache_provider.set_with_ttl(
            key=reset_password_otp_cache_key,
            value=Text.create(account_email_otp.value),
            ttl=self._reset_password_otp_ttl,
        )
        self._cache_provider.set(
            key=reset_password_otp_attempts_cache_key,
            value=Text.create(str(Otp.MAX_VERIFICATION_ATTEMPTS)),
        )
        self._cache_provider.set_with_ttl(
            key=reset_password_otp_resend_cooldown_cache_key,
            value=Text.create(account_email_otp.value),
            ttl=self._reset_password_otp_resend_cooldown_ttl,
        )

        self._broker.publish(
            PasswordResetRequestEvent(
                account_email=account.email.value,
                account_email_otp=account_email_otp.value,
            )
        )
