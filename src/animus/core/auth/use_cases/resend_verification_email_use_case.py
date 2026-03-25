from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.errors import AccountAlreadyVerifiedError
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.domain.structures import Email
from animus.core.auth.interfaces import AccountsRepository
from animus.core.shared.domain.structures import Text, Ttl
from animus.core.shared.interfaces import Broker, CacheProvider, OtpProvider


class ResendVerificationEmailUseCase:
    _OTP_LENGTH = 6

    def __init__(
        self,
        accounts_repository: AccountsRepository,
        otp_provider: OtpProvider,
        cache_provider: CacheProvider,
        broker: Broker,
        email_verification_otp_ttl: Ttl | None = None,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._otp_provider = otp_provider
        self._cache_provider = cache_provider
        self._broker = broker
        self._email_verification_otp_ttl = (
            email_verification_otp_ttl
            if email_verification_otp_ttl is not None
            else Ttl.create(3600)
        )

    def execute(self, email: str) -> None:
        account_email = Email.create(email)
        account = self._accounts_repository.find_by_email(account_email)

        if account.is_verified.is_true:
            raise AccountAlreadyVerifiedError

        account_email_otp = self._otp_provider.generate(length=self._OTP_LENGTH)
        email_verification_cache_key = CacheKeys().get_email_verification(
            account.email.value
        )
        self._cache_provider.set_with_ttl(
            key=email_verification_cache_key,
            value=Text.create(account_email_otp.value),
            ttl=self._email_verification_otp_ttl,
        )

        self._broker.publish(
            EmailVerificationRequestedEvent(
                account_email=account.email.value,
                account_email_otp=account_email_otp.value,
            )
        )
