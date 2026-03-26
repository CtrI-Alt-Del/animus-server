from animus.core.auth.domain.structures import Email, Otp
from animus.core.notification.interfaces import EmailSenderProvider


class SendAccountVerificationEmailUseCase:
    def __init__(self, email_sender_provider: EmailSenderProvider) -> None:
        self._email_sender_provider = email_sender_provider

    def execute(self, account_email: str, otp: str) -> None:
        self._email_sender_provider.send_account_verification_email(
            account_email=Email.create(account_email),
            otp=Otp.create(otp),
        )
