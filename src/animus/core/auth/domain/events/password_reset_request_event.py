from dataclasses import dataclass

from animus.core.shared.domain.abstracts.event import Event


@dataclass(frozen=True)
class _Payload:
    account_email: str
    account_email_otp: str


class PasswordResetRequestEvent(Event[_Payload]):
    name = 'auth/password-reset.requested'

    def __init__(self, account_email: str, account_email_otp: str) -> None:
        payload = _Payload(
            account_email=account_email,
            account_email_otp=account_email_otp,
        )
        super().__init__(PasswordResetRequestEvent.name, payload)
