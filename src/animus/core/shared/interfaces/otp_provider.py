from typing import Protocol

from animus.core.auth.domain.structures import Otp


class OtpProvider(Protocol):
    def generate(self, length: int) -> Otp: ...
