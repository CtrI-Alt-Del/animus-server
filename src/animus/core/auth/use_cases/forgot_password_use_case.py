from animus.core.auth.domain.events.password_reset_request_event import (
    PasswordResetRequestEvent,
)
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.shared.interfaces.broker import Broker


class ForgotPasswordUseCase:
    def __init__(self, accounts_repository: AccountsRepository, broker: Broker) -> None:
        self._accounts_repository = accounts_repository
        self._broker = broker

    def execute(self, email: str) -> None:
        account = self._accounts_repository.find_by_email(Email.create(email))
        if account is None:
            return
        self._broker.publish(PasswordResetRequestEvent(account_email=account.email))
