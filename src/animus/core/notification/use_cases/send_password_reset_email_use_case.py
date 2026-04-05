from animus.core.auth.domain.structures import Email
from animus.core.auth.interfaces.email_verification_provider import (
    EmailVerificationProvider,
)
from animus.core.notification.interfaces import EmailSenderProvider


class SendPasswordResetEmailUseCase:
    def __init__(
        self,
        email_sender_provider: EmailSenderProvider,
        email_verification_provider: EmailVerificationProvider,
    ) -> None:
        self._email_sender_provider = email_sender_provider
        self._email_verification_provider = email_verification_provider

    def execute(self, account_email: str) -> None:
        token = self._email_verification_provider.generate_verification_token(
            Email.create(account_email)
        )
        self._email_sender_provider.send_password_reset_email(
            account_email=Email.create(account_email), token=token
        )
