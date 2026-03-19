from typing import Protocol

from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.structures import Logical, Text


class EmailVerificationProvider(Protocol):
    def generate_verification_token(self, account_email: Email) -> Text: ...

    def verify_verification_token(self, verification_token: Text) -> Logical: ...

    def decode_email_from_token(self, verification_token: Text) -> Email: ...
