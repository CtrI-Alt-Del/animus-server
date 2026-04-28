from typing import Protocol

from animus.core.auth.domain.structures import Email, Otp


class EmailSenderProvider(Protocol):
    def send_account_verification_email(
        self,
        account_email: Email,
        otp: Otp,
    ) -> None: ...
    def send_password_reset_email(
        self,
        account_email: Email,
        otp: Otp,
    ) -> None: ...
