from typing import NamedTuple


class CacheKeys(NamedTuple):
    EMAIL_VERIFICATION = 'auth:email_verification'
    EMAIL_VERIFICATION_ATTEMPTS = 'auth:email_verification_attempts'
    RESET_PASSWORD_OTP = 'auth:reset_password_otp'
    RESET_PASSWORD_OTP_ATTEMPTS = 'auth:reset_password_otp_attempts'
    RESET_PASSWORD_OTP_RESEND_COOLDOWN = 'auth:reset_password_otp_resend_cooldown'
    RESET_PASSWORD_CONTEXT = 'auth:reset_password_context'

    def get_email_verification(self, email: str) -> str:
        return f'{self.EMAIL_VERIFICATION}:{email}'

    def get_email_verification_attempts(self, email: str) -> str:
        return f'{self.EMAIL_VERIFICATION_ATTEMPTS}:{email}'

    def get_reset_password_otp(self, email: str) -> str:
        return f'{self.RESET_PASSWORD_OTP}:{email}'

    def get_reset_password_otp_attempts(self, email: str) -> str:
        return f'{self.RESET_PASSWORD_OTP_ATTEMPTS}:{email}'

    def get_reset_password_otp_resend_cooldown(self, email: str) -> str:
        return f'{self.RESET_PASSWORD_OTP_RESEND_COOLDOWN}:{email}'

    def get_reset_password_context(self, reset_context: str) -> str:
        return f'{self.RESET_PASSWORD_CONTEXT}:{reset_context}'
