from animus.core.auth.domain.errors import AccountAlreadyVerifiedError
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.domain.structures import Email
from animus.core.auth.interfaces import AccountsRepository, EmailVerificationProvider
from animus.core.shared.interfaces import Broker


class ResendVerificationEmailUseCase:
    def __init__(
        self,
        accounts_repository: AccountsRepository,
        email_verification_provider: EmailVerificationProvider,
        broker: Broker,
    ) -> None:
        self._accounts_repository = accounts_repository
        self._email_verification_provider = email_verification_provider
        self._broker = broker

    def execute(self, email: str) -> None:
        account_email = Email.create(email)
        account = self._accounts_repository.find_by_email(account_email)

        if account.is_verified.is_true:
            raise AccountAlreadyVerifiedError

        verification_token = (
            self._email_verification_provider.generate_verification_token(account_email)
        )
        self._broker.publish(
            EmailVerificationRequestedEvent(
                account_email=account.email.value,
                account_email_verification_token=verification_token.value,
            )
        )
