from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import (
    AccountAlreadyExistsError,
)
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.domain.structures import Email, Otp, Password
from animus.core.auth.interfaces import (
    AccountsRepository,
    HashProvider,
)
from animus.core.shared.domain.structures import Name, Text, Ttl
from animus.core.shared.interfaces import Broker, CacheProvider, OtpProvider


class SignUpUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        hash_provider: HashProvider,
        otp_provider: OtpProvider,
        cache_provider: CacheProvider,
        broker: Broker,
        email_verification_otp_ttl: Ttl | None = None,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._hash_provider = hash_provider
        self._otp_provider = otp_provider
        self._cache_provider = cache_provider
        self._broker = broker
        self._email_verification_otp_ttl = (
            email_verification_otp_ttl
            if email_verification_otp_ttl is not None
            else Ttl.create(3600)
        )

    def execute(self, name: str, email: str, password: str) -> AccountDto:
        account_name = Name.create(name)
        account_email = Email.create(email)
        account_password = Password.create(password)

        existing_account = self._accounts_repository.find_by_email(account_email)
        if existing_account is not None:
            raise AccountAlreadyExistsError

        account = Account.create(
            AccountDto(
                name=account_name.value,
                email=account_email.value,
                password=account_password.value,
            )
        )

        password_hash = self._hash_provider.generate(
            Text.create(account_password.value)
        )
        self._accounts_repository.add(account, password_hash)

        account_email_otp = self._otp_provider.generate()
        email_verification_cache_key = CacheKeys().get_email_verification(
            account_email.value
        )
        email_verification_attempts_cache_key = (
            CacheKeys().get_email_verification_attempts(account_email.value)
        )
        self._cache_provider.set_with_ttl(
            key=email_verification_cache_key,
            value=Text.create(account_email_otp.value),
            ttl=self._email_verification_otp_ttl,
        )
        self._cache_provider.set(
            email_verification_attempts_cache_key,
            Text.create(str(Otp.MAX_VERIFICATION_ATTEMPTS)),
        )

        self._broker.publish(
            EmailVerificationRequestedEvent(
                account_email=account_email.value,
                account_email_otp=account_email_otp.value,
            )
        )

        return AccountDto(
            id=account.id.value,
            name=account.name.value,
            email=account.email.value,
            password=None,
            is_verified=account.is_verified.value,
            is_active=account.is_active.value,
            social_accounts=[item.dto for item in account.social_accounts],
        )
