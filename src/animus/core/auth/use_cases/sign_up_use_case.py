from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
)
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.domain.structures import Email, Password
from animus.core.auth.interfaces import (
    AccountsRepository,
    EmailVerificationProvider,
    HashProvider,
)
from animus.core.shared.domain.structures import Name, Text
from animus.core.shared.interfaces import Broker


class SignUpUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        hash_provider: HashProvider,
        email_verification_provider: EmailVerificationProvider,
        broker: Broker,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._hash_provider = hash_provider
        self._email_verification_provider = email_verification_provider
        self._broker = broker

    def execute(self, name: str, email: str, password: str) -> AccountDto:
        account_name = Name.create(name)
        account_email = Email.create(email)
        account_password = Password.create(password)

        try:
            self._accounts_repository.find_by_email(account_email)
        except AccountNotFoundError:
            pass
        else:
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

        verification_token = (
            self._email_verification_provider.generate_verification_token(account_email)
        )
        self._broker.publish(
            EmailVerificationRequestedEvent(
                account_email=account_email.value,
                account_email_verification_token=verification_token.value,
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
