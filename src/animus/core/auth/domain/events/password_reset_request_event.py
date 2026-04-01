from dataclasses import dataclass
from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.abstracts.event import Event


@dataclass(frozen=True)
class _Payload:
    account_email: Email

class PasswordResetRequestEvent(Event[_Payload]):
    name = 'auth/password-reset.requested'

    def __init__(self,account_email:Email)->None:
        payload = _Payload(
            account_email=account_email,
        )
        super().__init__(PasswordResetRequestEvent.name, payload)

