from typing import NamedTuple


class CacheKeys(NamedTuple):
    EMAIL_VERIFICATION_OTP = 'auth:email_verification'
    EMAIL_VERIFICATION = EMAIL_VERIFICATION_OTP

    def email_verification_otp(self, email: str) -> str:
        return f'{self.EMAIL_VERIFICATION_OTP}:{email}'

    def get_email_verification(self, email: str) -> str:
        return self.email_verification_otp(email)
