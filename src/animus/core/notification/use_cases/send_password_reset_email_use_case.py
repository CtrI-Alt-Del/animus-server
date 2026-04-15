from animus.core.auth.domain.structures import Email, Otp
from animus.core.notification.interfaces import EmailSenderProvider


class SendPasswordResetEmailUseCase:
    def __init__(
        self,
        email_sender_provider: EmailSenderProvider,
    ) -> None:
        self._email_sender_provider = email_sender_provider

    def execute(self, account_email: str, otp: str) -> None:
        normalized_account_email = Email.create(account_email)
        normalized_otp = Otp.create(otp)

        self._email_sender_provider.send_password_reset_email(
            account_email=normalized_account_email,
            otp=normalized_otp,
        )
