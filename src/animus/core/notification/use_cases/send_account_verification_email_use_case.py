from animus.core.auth.domain.structures import Email
from animus.core.notification.interfaces import EmailSenderProvider
from animus.core.shared.domain.structures import Text


class SendAccountVerificationEmailUseCase:
    def __init__(self, email_sender_provider: EmailSenderProvider) -> None:
        self._email_sender_provider = email_sender_provider

    def execute(self, account_email: str, verification_token: str) -> None:
        self._email_sender_provider.send_account_verification_email(
            account_email=Email.create(account_email),
            verification_token=Text.create(verification_token),
        )
