import secrets

from animus.core.auth.domain.structures import Otp
from animus.core.shared.interfaces import OtpProvider


class SecretsOtpProvider(OtpProvider):
    def generate(self) -> Otp:
        otp = ''.join(str(secrets.randbelow(10)) for _ in range(6))
        return Otp.create(otp)
