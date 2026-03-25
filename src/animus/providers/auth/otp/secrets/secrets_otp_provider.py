import secrets

from animus.core.auth.domain.structures import Otp
from animus.core.shared.interfaces import OtpProvider


class SecretsOtpProvider(OtpProvider):
    def generate(self, length: int) -> Otp:
        otp = ''.join(str(secrets.randbelow(10)) for _ in range(length))
        return Otp.create(otp)
