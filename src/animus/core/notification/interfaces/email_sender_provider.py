from typing import Protocol

from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.structures import Text


class EmailSenderProvider(Protocol):
    def send_account_verification_email(
        self,
        account_email: Email,
        verification_token: Text,
    ) -> None: ...
