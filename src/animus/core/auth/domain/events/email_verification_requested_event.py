from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    account_email: str
    account_email_otp: str


class EmailVerificationRequestedEvent(Event[_Payload]):
    name = 'auth/email-verification.requested'

    def __init__(
        self,
        account_email: str,
        account_email_otp: str,
    ) -> None:
        payload = _Payload(
            account_email=account_email,
            account_email_otp=account_email_otp,
        )
        super().__init__(EmailVerificationRequestedEvent.name, payload)
